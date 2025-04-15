from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol
from pydantic import BaseModel


@dataclass
class TextMessage:
    text: str

@dataclass
class FileMessage:
    file_path: str

class LanguageModel(Protocol):
    @abstractmethod
    async def chat(
            self,
            messages: list[TextMessage | FileMessage],
            system_prompt: str | None = None,
            schema: type[BaseModel] | None = None
    ):
        raise NotImplementedError
