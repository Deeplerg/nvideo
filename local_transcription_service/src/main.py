from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every
from faststream.rabbit import RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter, Logger
from .services.DownloadService import DownloadService
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

def get_transformer_model():
    global transformer_model
    if transformer_model is None:
        transformer_model = TransformerTranscriptionModel(AppConfiguration.TRANSCRIPTION_MODEL)
    return transformer_model

def get_faster_whisper_model():
    global faster_whisper_model
    if faster_whisper_model is None:
        faster_whisper_model = FasterWhisperTranscriptionModel(AppConfiguration.TRANSCRIPTION_MODEL)
    return faster_whisper_model

def get_transcription_service(model = Depends(get_faster_whisper_model)):
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

    result = transcription.transcribe(path)
    logger.info(f"Transcribed video {body.video_id}")

    await broker.publish(TranscriptionResult(
        job_id = body.job_id,
        result = result
    ), queue="transcription.result")