from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every
from faststream.rabbit.fastapi import RabbitRouter, Logger
from google import genai
from shared.language import *
from shared.models import SummaryResult
from .config import AppConfiguration
from shared.models import *
from .services.gemini_language_model import GeminiLanguageModel

router = RabbitRouter(AppConfiguration.AMQP_URL, fail_fast=False)
broker = router.broker
app = FastAPI()
app.include_router(router)

gemini_client : genai.Client | None = None

def get_gemini_client() -> genai.Client:
    global gemini_client

    if gemini_client is not None:
        return gemini_client

    return genai.Client(api_key=AppConfiguration.LANGUAGE_MODEL_PROVIDER_API_KEY)

def get_model(
        logger: Logger
) -> LanguageModel:
    provider = AppConfiguration.LANGUAGE_MODEL_PROVIDER
    match provider:
        case "google":
            client = get_gemini_client()
            return GeminiLanguageModel(get_language_model_name(), client, logger)
        case _:
            client = get_gemini_client()
            return GeminiLanguageModel(get_language_model_name(), client, logger)

def get_language_service(
        logger: Logger,
        model: LanguageModel = Depends(get_model)
):
    return LanguageService(
        logger=logger,
        model=model,
        summary_system_prompt=AppConfiguration.LANGUAGE_SUMMARY_SYSTEM_PROMPT,
        overall_summary_system_prompt=AppConfiguration.LANGUAGE_OVERALL_SUMMARY_SYSTEM_PROMPT,
        entity_system_prompt=AppConfiguration.LANGUAGE_ENTITY_SYSTEM_PROMPT,
        empty_chunk_threshold_ms=AppConfiguration.LANGUAGE_EMPTY_CHUNK_THRESHOLD_MS
    )

def get_language_model_name() -> str:
    return AppConfiguration.LANGUAGE_MODEL

def get_summary_model_name() -> str:
    return f"summary.remote-{AppConfiguration.LANGUAGE_MODEL_PROVIDER}-{AppConfiguration.LANGUAGE_MODEL}"

def get_entity_relation_model_name() -> str:
    return f"entity-relation.remote-{AppConfiguration.LANGUAGE_MODEL_PROVIDER}-{AppConfiguration.LANGUAGE_MODEL}"


@router.after_startup
async def startup(app: FastAPI):
    await broker.start()

    await publish_available_models()

@repeat_every(seconds=10)
async def publish_available_models():
    models = [
        get_summary_model_name(),
        get_entity_relation_model_name()
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

@router.subscriber(get_summary_model_name())
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

    response = SummaryResponse(
        job_id=body.job_id,
        result=SummaryResult(
            chunks=convert_to_chunk_results(chunks),
            overall_summary=overall_summary
        )
    )

    await broker.publish(response, queue="summary.result")

@router.subscriber(get_entity_relation_model_name())
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