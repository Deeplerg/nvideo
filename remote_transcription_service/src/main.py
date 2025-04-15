import logging
import os
from deepgram import DeepgramClient
from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every
from faststream.rabbit.fastapi import RabbitRouter, Logger
from shared.audio import *
from shared.transcription import *
from shared.models import *
from shared.transcription.utils import convert_to_chunk_results
from .services.GeminiTranscriptionModel import GeminiTranscriptionModel
from .services.DeepgramTranscriptionModel import DeepgramTranscriptionModel
from .config import AppConfiguration
from google import genai


router = RabbitRouter(AppConfiguration.AMQP_URL, fail_fast=False)
broker = router.broker
app = FastAPI()
app.include_router(router)

def get_deepgram_client() -> DeepgramClient:
    return DeepgramClient(api_key=AppConfiguration.DEEPGRAM_TRANSCRIPTION_API_KEY)

def get_gemini_client() -> genai.Client:
    return genai.Client(api_key=AppConfiguration.GEMINI_TRANSCRIPTION_API_KEY)

def get_custom_logger(name: str | None) -> logging.Logger:
    return logging.getLogger(name)

def get_deepgram_model() -> DeepgramTranscriptionModel:
    client = get_deepgram_client()
    logger = get_custom_logger("deepgram")
    return DeepgramTranscriptionModel(logger, AppConfiguration.DEEPGRAM_TRANSCRIPTION_MODEL, client)

def get_gemini_model() -> GeminiTranscriptionModel:
    client = get_gemini_client()
    logger = get_custom_logger("gemini")
    return GeminiTranscriptionModel(logger, AppConfiguration.GEMINI_TRANSCRIPTION_MODEL, client)

def get_transcription_service():
    model: TranscriptionModel
    match AppConfiguration.TRANSCRIPTION_PROVIDER:
        case "deepgram":
            model = get_deepgram_model()
        case "google":
            model = get_gemini_model()
        case _:
            model = get_gemini_model()

    return TranscriptionService(model)

def get_download_service():
    return DownloadService()

def get_model_name() -> str:
    match AppConfiguration.TRANSCRIPTION_PROVIDER:
        case "deepgram":
            transcription_model = AppConfiguration.DEEPGRAM_TRANSCRIPTION_MODEL
        case "google":
            transcription_model = AppConfiguration.GEMINI_TRANSCRIPTION_MODEL
        case _:
            transcription_model = AppConfiguration.GEMINI_TRANSCRIPTION_MODEL

    model_name = f"transcription.remote-{AppConfiguration.TRANSCRIPTION_PROVIDER}-{transcription_model}"
    return model_name

@router.after_startup
async def startup(app: FastAPI):
    await broker.connect()
    await broker.start()

    await publish_available_models()

@repeat_every(seconds=10)
async def publish_available_models():
    await broker.publish(ModelAvailable(
        model_name=get_model_name()
    ), queue="model.available")

@router.subscriber(get_model_name())
async def transcribe_remote_deepgram(
        body: TranscriptionRequest,
        logger: Logger,
        download: DownloadService = Depends(get_download_service),
        transcription: TranscriptionService = Depends(get_transcription_service)
):
    logger.info(f"Handling transcription request for {body.video_id}...")

    path = download.download_video_by_id(body.video_id)
    logger.info(f"Downloaded {body.video_id} to {path}")

    segment_length_ms = AppConfiguration.TRANSCRIPTION_CHUNK_SECONDS * 1000

    chunks = transcription.transcribe(path, segment_length_ms)
    logger.info(f"Transcribed video {body.video_id}")

    response=TranscriptionResponse(
        job_id = body.job_id,
        result = convert_to_chunk_results(chunks)
    )

    await broker.publish(response, queue="transcription.result")

    if os.path.exists(path):
        os.remove(path)