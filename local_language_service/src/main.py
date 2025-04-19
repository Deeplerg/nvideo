from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every
from faststream.rabbit.fastapi import RabbitRouter, Logger
from ollama import AsyncClient
from shared.language import *
from shared.models import SummaryResult
from .config import AppConfiguration
from shared.models import *
from .services.ollama_language_model import OllamaLanguageModel


language_model = AppConfiguration.LANGUAGE_MODEL
language_model_name = language_model.split(':')[0]
summary_model_name = f"summary.local-{language_model_name}"
entity_relation_model_name = f"entity-relation.local-{language_model_name}"


router = RabbitRouter(AppConfiguration.AMQP_URL, fail_fast=False)
broker = router.broker
app = FastAPI()
app.include_router(router)

ollama_client : AsyncClient | None = None

def get_ollama_client():
    global ollama_client

    if ollama_client is not None:
        return ollama_client

    host = AppConfiguration.OLLAMA_HOST
    port = AppConfiguration.OLLAMA_PORT

    ollama_client = AsyncClient(
        host=f"http://{host}:{port}"
    )
    return ollama_client

def get_ollama_model(
        client = Depends(get_ollama_client)
):
    return OllamaLanguageModel(language_model, client)

def get_language_service(
        logger: Logger,
        model = Depends(get_ollama_model)
):
    return LanguageService(
        logger=logger,
        model=model,
        summary_system_prompt=AppConfiguration.LANGUAGE_SUMMARY_SYSTEM_PROMPT,
        overall_summary_system_prompt=AppConfiguration.LANGUAGE_OVERALL_SUMMARY_SYSTEM_PROMPT,
        entity_system_prompt=AppConfiguration.LANGUAGE_ENTITY_SYSTEM_PROMPT,
        empty_chunk_threshold_ms=AppConfiguration.LANGUAGE_EMPTY_CHUNK_THRESHOLD_MS
    )

async def pull_model(client: AsyncClient, model: str):
    await client.pull(
        model=model,
        stream=False
    )


@router.after_startup
async def startup(app: FastAPI):
    await broker.start()

    await publish_available_models()

    client = get_ollama_client()
    await pull_model(client, language_model)

@repeat_every(seconds=10)
async def publish_available_models():
    models = [
        summary_model_name,
        entity_relation_model_name
    ]

    for model in models:
        await broker.publish(ModelAvailable(
            model_name=model
        ), queue="model.available")

def convert_to_chunk_results(chunks: list[ChunkSummaryResponse]) -> list[ChunkSummaryResult]:
    return [
        ChunkSummaryResult(
            text=chunk.text,
            start_time_ms=chunk.start_time_ms,
            end_time_ms=chunk.end_time_ms
        )
        for chunk in chunks
    ]

@router.subscriber(summary_model_name)
async def summarize_local(
        body : SummaryRequest,
        logger: Logger,
        language: LanguageService = Depends(get_language_service)
):
    logger.info(f"Handling summary request for {body.video_id}...")

    chunks = await language.summarize(body.transcription)

    is_overall_summary_needed = len(chunks) > 1
    logger.info(f"Summarized chunks of video {body.video_id}. Overall summary needed: {is_overall_summary_needed}")

    overall_summary: str | None = None
    if is_overall_summary_needed:
        overall_summary = await language.generate_overall_summary(chunks)
        logger.info(f"Generated overall summary of video {body.video_id}")

    logger.info(f"Summarized video {body.video_id}")

    response=SummaryResponse(
        job_id = body.job_id,
        result = SummaryResult(
            chunks=convert_to_chunk_results(chunks),
            overall_summary = overall_summary
        )
    )

    await broker.publish(response, queue="summary.result")

@router.subscriber(entity_relation_model_name)
async def entity_local(
        body : EntityRelationRequest,
        logger: Logger,
        language: LanguageService = Depends(get_language_service)
):
    logger.info(f"Handling entity-relation request for {body.video_id}...")

    entity_relations = await language.generate_entity_relations(body.transcription)
    logger.info(f"Generated entity-relations for video {body.video_id}")

    result=entity_relations.to_result()

    response=EntityRelationResponse(
        job_id=body.job_id,
        result=result
    )

    await broker.publish(response, queue="entity-relation.result")