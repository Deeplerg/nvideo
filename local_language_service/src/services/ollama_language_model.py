from ollama import AsyncClient, ChatResponse
from pydantic import BaseModel
from shared.language.language_model import LanguageModel, TextMessage, FileMessage


class OllamaLanguageModel(LanguageModel):
    def __init__(
            self,
            model_name: str,
            client: AsyncClient
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

        if system_prompt:
            contents.append({"role": "system", "content": system_prompt})

        for message in messages:
            if isinstance(message, TextMessage):
                contents.append({"role": "user", "content": message.text})
                continue
            if isinstance(message, FileMessage):
                file_path = message.file_path
                with open(file_path, "r") as file:
                    file_content = file.read()

                contents.append({"role": "user", "content": file_content})
                continue

        response: ChatResponse = await self.__client.chat(
            model=self.__model_name,
            messages=contents,
            format=schema.model_json_schema() if schema else None,
            stream=False,
        )

        return response.message.content