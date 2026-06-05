import json
from logging import Logger
from pydantic import BaseModel
from openai import AsyncOpenAI
from shared.language.language_model import LanguageModel, TextMessage, FileMessage

class OpenAILanguageModel(LanguageModel):
    def __init__(self, model_name: str, client: AsyncOpenAI, logger: Logger):
        self.__model_name = model_name
        self.__client = client
        self.__logger = logger

    async def chat(self,
                   messages: list[TextMessage | FileMessage],
                   system_prompt: str | None = None,
                   schema: type[BaseModel] | None = None) -> str:
        api_messages = []

        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            if isinstance(msg, TextMessage):
                api_messages.append({"role": "user", "content": msg.text})
            elif isinstance(msg, FileMessage):
                with open(msg.file_path, "r") as file:
                    api_messages.append({"role": "user", "content": file.read()})

        kwargs = {}
        if schema:
            api_messages.append({
                "role": "user",
                "content": f"Respond ONLY with valid JSON matching exactly this schema: {json.dumps(schema.model_json_schema())}"
            })
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.__client.chat.completions.create(
            model=self.__model_name,
            messages=api_messages,
            **kwargs
        )

        return response.choices[0].message.content