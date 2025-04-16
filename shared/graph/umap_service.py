from numpy import ndarray
from umap import UMAP

class UMAPService:
    def __init__(
            self,
            neighbours: int
    ):
        self.__umap = UMAP(n_components=2, n_neighbors=neighbours, min_dist=1)

    def reduce(self, embeddings: ndarray):
        return self.__umap.fit_transform(embeddings)