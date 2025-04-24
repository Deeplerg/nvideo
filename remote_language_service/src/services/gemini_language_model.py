from logging import Logger
from google import genai
from google.genai.types import GenerateContentConfigDict
from pydantic import BaseModel
from shared.api_helpers import GeminiHelper
from shared.language.language_model import LanguageModel, TextMessage, FileMessage


class GeminiLanguageModel(LanguageModel):
    def __init__(
            self,
            model_name: str,
            client: genai.Client,
            logger: Logger
    ):
        self.__model_name = model_name
        self.__client = client
        self.__logger = logger
        self.__helper = GeminiHelper(logger, client)

    async def chat(
            self,
            messages: list[TextMessage | FileMessage],
            system_prompt: str | None = None,
            schema: type[BaseModel] | None = None
    ) -> str:
        contents = []
        for message in messages:
            if isinstance(message, TextMessage):
                contents.append(message.text)
                continue
            if isinstance(message, FileMessage):
                file_path = message.file_path
                uploaded_file = await self.__client.aio.files.upload(file=file_path)
                contents.append(uploaded_file)
                continue

        config : GenerateContentConfigDict | None = None

        if not self.__model_name.startswith("gemini"):
            if schema:
                contents.append(str(schema.model_json_schema()))
            config = None
        else:
            config = GenerateContentConfigDict(
                    system_instruction=system_prompt,
                    response_mime_type="application/json" if schema else None,
                    response_schema=schema
            )

        response = await self.__helper.generate_with_retry_and_congestion_backoff(
            model_name=self.__model_name,
            contents=contents,
            config=config
        )

        return response.text