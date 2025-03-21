from sklearn.manifold import TSNE
from ..config import AppConfiguration

class TSNEService:
    def __init__(self):
        perplexity = AppConfiguration.GRAPH_TSNE_PERPLEXITY
        self.__tsne = TSNE(n_components=2, perplexity=perplexity)

    def reduce(self, embeddings):
        return self.__tsne.fit_transform(embeddings)