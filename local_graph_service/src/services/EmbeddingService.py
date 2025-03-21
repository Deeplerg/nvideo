import gc
import torch.cuda
from numpy import ndarray
from sentence_transformers import SentenceTransformer
from ..config import AppConfiguration

class EmbeddingService:
    def __init__(self):
        self.__model: SentenceTransformer | None = None

    def ensure_loaded(self):
        if self.__model is None:
            self.__load()

    def __load(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_name = AppConfiguration.GRAPH_EMBED_MODEL
        self.__model = SentenceTransformer(model_name, device=device)

    def unload(self):
        del self.__model
        self.__model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def embed(self, entities: list[str]) -> ndarray:
        self.ensure_loaded()
        return self.__model.encode(entities)