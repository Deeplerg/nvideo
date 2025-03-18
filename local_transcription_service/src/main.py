import asyncio
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
import os
from faststream.rabbit import RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter, Logger
from models import *


class AppConfiguration:
    AMQP_URL: str = os.getenv("AMQP_URL")


router = RabbitRouter(AppConfiguration.AMQP_URL)
broker = RabbitBroker(AppConfiguration.AMQP_URL)
app = FastAPI()
app.include_router(router)


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
        logger: Logger
):
    logger.info(f"Handling transcription request for {body.video_id}...")

    await asyncio.sleep(10) # "work"

    await broker.publish(TranscriptionResult(
        job_id = body.job_id,
        result = "Once upon a time..."
    ), queue="transcription.result")

    logger.info(f"Transcribed video {body.video_id}")