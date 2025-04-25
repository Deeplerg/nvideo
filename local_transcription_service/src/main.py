import asyncio
import os
from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every
from faststream.rabbit.fastapi import RabbitRouter, Logger
from shared.audio import *
from shared.transcription import *
from shared.transcription.utils import convert_to_chunk_results
from shared.models import *
from .services.transformer_transcription_model import TransformerTranscriptionModel
from .services.faster_whisper_transcription_model import FasterWhisperTranscriptionModel
from .config import AppConfiguration


transcription_model = AppConfiguration.TRANSCRIPTION_MODEL
transcription_model_full_name = "transcription.local-whisper"


router = RabbitRouter(AppConfiguration.AMQP_URL, fail_fast=False)
broker = router.broker
app = FastAPI()
app.include_router(router)

transformer_model : TransformerTranscriptionModel | None = None
faster_whisper_model : FasterWhisperTranscriptionModel | None = None

def get_transformer_model() -> TransformerTranscriptionModel:
    global transformer_model
    if transformer_model is None:
        transformer_model = TransformerTranscriptionModel(transcription_model)
    return transformer_model

def get_faster_whisper_model() -> FasterWhisperTranscriptionModel:
    global faster_whisper_model
    if faster_whisper_model is None:
        faster_whisper_model = FasterWhisperTranscriptionModel(transcription_model)
    return faster_whisper_model

def get_transcription_service():
    model: TranscriptionModel
    match AppConfiguration.TRANSCRIPTION_LIBRARY:
        case "transformers":
            model = get_transformer_model()
        case "faster_whisper":
            model = get_faster_whisper_model()
        case _:
            model = get_transformer_model()

    return TranscriptionService(model)

def get_download_service():
    return DownloadService()

@router.after_startup
async def startup(app: FastAPI):
    await broker.connect()
    await broker.start()

    await publish_available_models()

@repeat_every(seconds=10)
async def publish_available_models():
    models = [ transcription_model_full_name ]

    for model in models:
        await broker.publish(ModelAvailable(
            model_name=model
        ), queue="model.available")

@router.subscriber(transcription_model_full_name)
async def transcribe_local_whisper(
        body: TranscriptionRequest,
        logger: Logger,
        download: DownloadService = Depends(get_download_service),
        transcription: TranscriptionService = Depends(get_transcription_service)
):
    logger.info(f"Handling transcription request for {body.video_id}...")

    path = await asyncio.to_thread(download.download_video_by_id, body.video_id)
    logger.info(f"Downloaded {body.video_id} to {path}")

    segment_length_ms = AppConfiguration.TRANSCRIPTION_CHUNK_SECONDS * 1000

    chunks = list()
    async for chunk in transcription.transcribe(path, segment_length_ms):
        chunks.append(chunk)
        logger.info(f"Transcribed chunk at {chunk.start_time_ms} of {body.video_id}")
    logger.info(f"Transcribed video {body.video_id}")

    response=TranscriptionResponse(
        job_id = body.job_id,
        result = convert_to_chunk_results(chunks)
    )

    await broker.publish(response, queue="transcription.result")

    if os.path.exists(path):
        os.remove(path)