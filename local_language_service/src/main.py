from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every
from faststream.rabbit.fastapi import RabbitRouter, Logger
from ollama import AsyncClient
from .services.LanguageService import LanguageService, ChunkSummaryResponse
from .config import AppConfiguration
from shared.models import *

router = RabbitRouter(AppConfiguration.AMQP_URL, fail_fast=False)
broker = router.broker
app = FastAPI()
app.include_router(router)

language_model_name = AppConfiguration.LANGUAGE_MODEL.split(':')[0]
summary_model_name = f"summary.local-{language_model_name}"
entity_relation_model_name = f"entity-relation.local-{language_model_name}"

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

def get_language_service(
        logger: Logger,
        client = Depends(get_ollama_client)
):
    return LanguageService(
        client=client,
        logger=logger)

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
    await pull_model(client, AppConfiguration.LANGUAGE_MODEL)

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

@router.subscriber(f"summary.local-{language_model_name}")
async def summarize_local(
        body : SummaryRequest,
        logger: Logger,
        language: LanguageService = Depends(get_language_service)
):
    logger.info(f"Handling summary request for {body.video_id}...")

    chunks = await language.summarize(body.transcription)
    logger.info(f"Summarized video {body.video_id}")

    response=SummaryResponse(
        job_id = body.job_id,
        result = convert_to_chunk_results(chunks)
    )

    await broker.publish(response, queue="summary.result")

@router.subscriber(f"entity-relation.local-{language_model_name}")
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