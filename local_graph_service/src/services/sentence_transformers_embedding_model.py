import gc
import torch.cuda
from numpy import ndarray
from sentence_transformers import SentenceTransformer
from shared.graph.embedding_model import EmbeddingModel

class SentenceTransformersEmbeddingModel(EmbeddingModel):
    def __init__(
            self,
            embed_model: str,
            embed_model_dir: str
    ):
        self.__model: SentenceTransformer | None = None
        self.__embed_model = embed_model
        self.__embed_model_dir = embed_model_dir

    def ensure_loaded(self):
        if self.__model is None:
            self.__load()

    def __load(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_name = self.__embed_model
        cache_dir = self.__embed_model_dir
        self.__model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=cache_dir
        )

    def unload(self):
        del self.__model
        self.__model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def embed(self, entities: list[str]) -> ndarray:
        self.ensure_loaded()
        return self.__model.encode(entities)