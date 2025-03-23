from umap import UMAP
from ..config import AppConfiguration

class UMAPService:
    def __init__(self):
        neigh = AppConfiguration.GRAPH_UMAP_NEIGHBOURS
        self.__umap = UMAP(n_components=2, n_neighbors=neigh, min_dist=1)

    def reduce(self, embeddings):
        return self.__umap.fit_transform(embeddings)