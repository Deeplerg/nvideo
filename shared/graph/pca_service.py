from numpy import ndarray
from sklearn.decomposition import PCA

class PCAService:
    def __init__(
            self,
            max_dimensions: int
    ):
        self.__max_dimensions = max_dimensions

    def reduce(self, embeddings: ndarray):
        dim = self.__max_dimensions
        n_components = min(dim, embeddings.shape[0], embeddings.shape[1])
        pca = PCA(n_components=n_components)
        return pca.fit_transform(embeddings)