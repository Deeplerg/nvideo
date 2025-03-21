import os

class AppConfiguration:
    AMQP_URL: str = os.getenv("AMQP_URL")
    GRAPH_EMBED_MODEL : str = os.getenv("GRAPH_EMBED_MODEL")
    GRAPH_USE_PCA : bool = bool(os.getenv("GRAPH_USE_PCA"))
    GRAPH_FAVOR_UMAP : bool = bool(os.getenv("GRAPH_FAVOR_UMAP"))
    GRAPH_PCA_MAX_DIMENSIONS : int = int(os.getenv("GRAPH_PCA_MAX_DIMENSIONS"))
    GRAPH_UMAP_NEIGHBOURS : int = int(os.getenv("GRAPH_UMAP_NEIGHBOURS"))
    GRAPH_TSNE_PERPLEXITY : int = int(os.getenv("GRAPH_TSNE_PERPLEXITY"))