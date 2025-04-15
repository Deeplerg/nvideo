from abc import abstractmethod
from typing import Protocol


class TranscriptionModel(Protocol):
    @abstractmethod
    def ensure_loaded(self):
        raise NotImplementedError

    @abstractmethod
    def unload(self):
        raise NotImplementedError

    @abstractmethod
    def transcribe(self, file_path):
        raise NotImplementedError