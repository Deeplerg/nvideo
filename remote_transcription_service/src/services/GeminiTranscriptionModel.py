from logging import Logger
import httpx
from google import genai
from google.genai.types import GenerateContentConfigDict, GenerateContentResponse
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

        if "/" in self.__model_name:
            self.__model_name = self.__model_name.split('/')[-1]

    def ensure_loaded(self):
        pass

    def unload(self):
        pass

    def transcribe(self, file_path):
        audio = self.__client.files.upload(file=file_path)
        prompt = AppConfiguration.GEMINI_TRANSCRIPTION_PROMPT

        response : GenerateContentResponse | None = None
        retries = 5
        for i in range(1, retries):
            try:
                response = self.__client.models.generate_content(
                    model=self.__model_name,
                    contents=audio,
                    config=GenerateContentConfigDict(
                        system_instruction=prompt
                    )
                )
                break
            except httpx.ReadTimeout | httpx.ReadError:
                self.__logger.info(f"Read error. Retrying ({i} out of {retries})")

        result = response.text

        return result