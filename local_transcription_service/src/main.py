import os

from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every
from faststream.rabbit import RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter, Logger
from .services.DownloadService import DownloadService
from .services.TranscriptionChunk import TranscriptionChunk
from .services.TranscriptionModel import TranscriptionModel
from .services.TranscriptionService import TranscriptionService
from .services.TransformerTranscriptionModel import TransformerTranscriptionModel
from .services.FasterWhisperTranscriptionModel import FasterWhisperTranscriptionModel
from .config import AppConfiguration
from .models import *


router = RabbitRouter(AppConfiguration.AMQP_URL)
broker = RabbitBroker(AppConfiguration.AMQP_URL)
app = FastAPI()
app.include_router(router)

transformer_model : TransformerTranscriptionModel | None = None
faster_whisper_model : FasterWhisperTranscriptionModel | None = None

def get_transformer_model() -> TransformerTranscriptionModel:
    global transformer_model
    if transformer_model is None:
        transformer_model = TransformerTranscriptionModel(AppConfiguration.TRANSCRIPTION_MODEL)
    return transformer_model

def get_faster_whisper_model() -> FasterWhisperTranscriptionModel:
    global faster_whisper_model
    if faster_whisper_model is None:
        faster_whisper_model = FasterWhisperTranscriptionModel(AppConfiguration.TRANSCRIPTION_MODEL)
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
    await broker.start()

    await publish_available_models()

@repeat_every(seconds=10)
async def publish_available_models():
    models = [ "transcription.local-whisper" ]

    for model in models:
        await broker.publish(ModelAvailable(
            model_name=model
        ), queue="model.available")

def convert_to_chunk_results(chunks: list[TranscriptionChunk]) -> list[TranscriptionChunkResult]:
    return [
        TranscriptionChunkResult(
            text=chunk.text,
            start_time_ms=chunk.start_time_ms,
            end_time_ms=chunk.end_time_ms
        )
        for chunk in chunks
    ]

@router.subscriber("transcription.local-whisper")
async def transcribe_local_whisper(
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