import os

class AppConfiguration:
    __RMQ_USER: str = os.getenv("RABBITMQ_USER")
    __RMQ_PASS: str = os.getenv("RABBITMQ_PASS")
    __RMQ_PROTO: str = os.getenv("RABBITMQ_PROTO")
    __RMQ_HOST: str = os.getenv("RABBITMQ_HOST")
    __RMQ_PORT: str = os.getenv("RABBITMQ_PORT")
    AMQP_URL: str = f"{__RMQ_PROTO}://{__RMQ_USER}:{__RMQ_PASS}@{__RMQ_HOST}:{__RMQ_PORT}/"
    GRAPH_EMBED_MODEL : str = os.getenv("GRAPH_EMBED_MODEL")
    GRAPH_EMBED_MODEL_DIR : str = os.getenv("GRAPH_EMBED_MODEL_DIR")
    GRAPH_USE_PCA : bool = os.getenv("GRAPH_USE_PCA") == "True"
    GRAPH_FAVOR_UMAP : bool = bool(os.getenv("GRAPH_FAVOR_UMAP"))
    GRAPH_PCA_MAX_DIMENSIONS : int = int(os.getenv("GRAPH_PCA_MAX_DIMENSIONS"))
    GRAPH_UMAP_NEIGHBOURS : int = int(os.getenv("GRAPH_UMAP_NEIGHBOURS"))
    GRAPH_TSNE_PERPLEXITY : int = int(os.getenv("GRAPH_TSNE_PERPLEXITY"))