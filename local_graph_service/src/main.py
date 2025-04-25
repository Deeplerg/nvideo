import asyncio
from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every
from faststream.rabbit.fastapi import RabbitRouter, Logger
from shared.api_helpers.decorators import fail_job_on_exception
from .config import AppConfiguration
from shared.models import *
from shared.graph import *
from .services.sentence_transformers_embedding_model import SentenceTransformersEmbeddingModel

embed_model = AppConfiguration.GRAPH_EMBED_MODEL
embed_model_full_name = f"graph.local-{embed_model}"


router = RabbitRouter(AppConfiguration.AMQP_URL, fail_fast=False)
broker = router.broker
app = FastAPI()
app.include_router(router)


embedding_model: EmbeddingModel | None = None
pca_service: PCAService | None = None
tsne_service: TSNEService | None = None
umap_service: UMAPService | None = None

def get_embedding_model() -> EmbeddingModel:
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformersEmbeddingModel(
            embed_model=embed_model,
            embed_model_dir=AppConfiguration.GRAPH_EMBED_MODEL_DIR
        )
    return embedding_model

def get_pca_service() -> PCAService:
    global pca_service
    if pca_service is None:
        pca_service = PCAService(
            max_dimensions=AppConfiguration.GRAPH_PCA_MAX_DIMENSIONS
        )
    return pca_service

def get_tsne_service() -> TSNEService:
    global tsne_service
    if tsne_service is None:
        tsne_service = TSNEService(
            perplexity=AppConfiguration.GRAPH_TSNE_PERPLEXITY
        )
    return tsne_service

def get_umap_service() -> UMAPService:
    global umap_service
    if umap_service is None:
        umap_service = UMAPService(
            neighbours=AppConfiguration.GRAPH_UMAP_NEIGHBOURS
        )
    return umap_service

def get_graph_service(
        logger: Logger,
        embed = Depends(get_embedding_model),
        pca = Depends(get_pca_service),
        tsne = Depends(get_tsne_service),
        umap = Depends(get_umap_service)
):
    return GraphService(
        logger=logger,
        embed=embed,
        pca=pca,
        tsne=tsne,
        umap=umap,
        use_pca=AppConfiguration.GRAPH_USE_PCA,
        favor_umap=AppConfiguration.GRAPH_FAVOR_UMAP,
        external_reduction=False
    )


@router.after_startup
async def startup(app: FastAPI):
    await broker.start()

    await publish_available_models()

@repeat_every(seconds=10)
async def publish_available_models():
    models = [ embed_model_full_name ]

    for model in models:
        await broker.publish(ModelAvailable(
            model_name=model
        ), queue="model.available")

@router.subscriber(embed_model_full_name)
@fail_job_on_exception(broker=broker)
async def graph_local(
        body : GraphRequest,
        logger: Logger,
        graph_service: GraphService = Depends(get_graph_service)
):
    logger.info(f"Handling graph request for {body.video_id}...")

    graph = await asyncio.to_thread(graph_service.generate_graph, body.entity_relations)
    logger.info(f"Made a set of points for video {body.video_id}")

    result=graph.to_result()

    await broker.publish(GraphResponse(
        job_id=body.job_id,
        result=result
    ), queue="graph.result")