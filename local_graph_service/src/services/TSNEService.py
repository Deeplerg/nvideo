from sklearn.manifold import TSNE
from ..config import AppConfiguration

class TSNEService:
    def __init__(self):
        perplexity = AppConfiguration.GRAPH_TSNE_PERPLEXITY
        self.__tsne = TSNE(n_components=2, perplexity=perplexity)
        self.__tsne_low_perplexity = TSNE(n_components=2, perplexity=1)

    def reduce(self, embeddings):
        tsne = self.__tsne if embeddings.shape[0] > 2 else self.__tsne_low_perplexity
        return tsne.fit_transform(embeddings)