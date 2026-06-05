from logging import Logger
from openai import AsyncOpenAI
from shared.transcription import TranscriptionModel

class OpenAITranscriptionModel(TranscriptionModel):
    def __init__(self, logger: Logger, model_name: str, client: AsyncOpenAI):
        self.__logger = logger
        self.__model_name = model_name
        self.__client = client

    def ensure_loaded(self):
        pass

    def unload(self):
        pass

    async def transcribe(self, file_path: str):
        with open(file_path, "rb") as audio_file:
            response = await self.__client.audio.transcriptions.create(
                file=audio_file,
                model=self.__model_name,
                response_format="text"
            )
        return response