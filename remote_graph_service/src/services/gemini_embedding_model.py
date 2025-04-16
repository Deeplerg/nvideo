import numpy as np
from google import genai
from google.genai.types import EmbedContentConfig
from numpy import ndarray
from shared.graph.embedding_model import EmbeddingModel
from ..config import AppConfiguration

class GeminiEmbeddingModel(EmbeddingModel):
    def __init__(
            self,
            client: genai.Client,
            model_name: str
    ):
        self.__client = client
        self.__model_name = model_name

    def ensure_loaded(self):
        pass

    def unload(self):
        pass

    def embed(self, entities: list[str]) -> ndarray:
        result = self.__client.models.embed_content(
            model=self.__model_name,
            contents=entities,
            config=EmbedContentConfig(
                output_dimensionality=2
            ) if AppConfiguration.GRAPH_REDUCE_WITH_API else None
        )

        return np.array([embed.values for embed in result.embeddings])