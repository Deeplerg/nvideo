from numpy import ndarray
from sklearn.decomposition import PCA
from ..config import AppConfiguration

class PCAService:
    def reduce(self, embeddings: ndarray):
        dim = AppConfiguration.GRAPH_PCA_MAX_DIMENSIONS
        n_components = min(dim, embeddings.shape[0], embeddings.shape[1])
        pca = PCA(n_components=n_components)
        return pca.fit_transform(embeddings)