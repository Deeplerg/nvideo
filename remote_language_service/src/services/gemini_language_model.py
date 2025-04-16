from google import genai
from google.genai.types import GenerateContentConfigDict
from pydantic import BaseModel
from shared.language.language_model import LanguageModel, TextMessage, FileMessage


class GeminiLanguageModel(LanguageModel):
    def __init__(
            self,
            model_name: str,
            client: genai.Client
    ):
        self.__model_name = model_name
        self.__client = client

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

        if not self.__model_name.startswith("gemini"):
            if schema:
                contents.append(str(schema.model_json_schema()))

            response = await self.__client.aio.models.generate_content(
                model=self.__model_name,
                contents=contents,

            )
        else:
            response = await self.__client.aio.models.generate_content(
                model=self.__model_name,
                contents=contents,
                config=GenerateContentConfigDict(
                    system_instruction=system_prompt,
                    response_mime_type="application/json" if schema else None,
                    response_schema=schema
                )
            )

        return response.text