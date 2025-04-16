from abc import abstractmethod
from typing import Protocol
from numpy import ndarray

class EmbeddingModel(Protocol):
    @abstractmethod
    def ensure_loaded(self):
        pass

    @abstractmethod
    def unload(self):
        pass

    @abstractmethod
    def embed(self, entities: list[str]) -> ndarray:
        pass