from logging import Logger
from google import genai
from google.genai.types import GenerateContentConfigDict, GenerateContentResponse
from shared.api_helpers.gemini import GeminiHelper
from ..config import AppConfiguration
from shared.transcription import TranscriptionModel

class GeminiTranscriptionModel(TranscriptionModel):
    def __init__(
            self,
            logger: Logger,
            model_name: str,
            client: genai.Client):
        self.__logger = logger
        self.__model_name : str = model_name
        self.__client = client
        self.__helper = GeminiHelper(logger, client)

        if "/" in self.__model_name:
            self.__model_name = self.__model_name.split('/')[-1]

    def ensure_loaded(self):
        pass

    def unload(self):
        pass

    async def transcribe(self, file_path):
        audio = await self.__client.aio.files.upload(file=file_path)
        prompt = AppConfiguration.LLM_TRANSCRIPTION_PROMPT
        config = GenerateContentConfigDict(
            system_instruction=prompt
        )

        response = await self.__helper.generate_with_retry_and_congestion_backoff(self.__model_name, audio, config)

        result = response.text

        try:
            await self.__client.aio.files.delete(name=audio.name)
        except Exception:
            self.__logger.warning(f"Failed to clean up file.", exc_info=True)

        return result