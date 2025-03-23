from fastapi import FastAPI, Depends
from fastapi_utils.tasks import repeat_every
from faststream.rabbit import RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter, Logger
from .services.EmbeddingService import EmbeddingService
from .services.GraphService import GraphService
from .config import AppConfiguration
from .models import *
from .services.PCAService import PCAService
from .services.TSNEService import TSNEService
from .services.UMAPService import UMAPService


embed_model_name = AppConfiguration.GRAPH_EMBED_MODEL


router = RabbitRouter(AppConfiguration.AMQP_URL)
broker = RabbitBroker(AppConfiguration.AMQP_URL)
app = FastAPI()
app.include_router(router)


def get_embedding_service():
    return EmbeddingService()

def get_pca_service():
    return PCAService()

def get_tsne_service():
    return TSNEService

def get_umap_service():
    return UMAPService()

def get_graph_service(
        logger: Logger,
        embed = Depends(get_embedding_service),
        pca = Depends(get_pca_service),
        tsne = Depends(get_tsne_service),
        umap = Depends(get_umap_service)
):
    return GraphService(
        logger=logger,
        embed=embed,
        pca=pca,
        tsne=tsne,
        umap=umap
    )


@router.after_startup
async def startup(app: FastAPI):
    await broker.start()

    await publish_available_models()

@repeat_every(seconds=10)
async def publish_available_models():
    models = [ f"graph.local-{embed_model_name}" ]

    for model in models:
        await broker.publish(ModelAvailable(
            model_name=model
        ), queue="model.available")

@router.subscriber(f"graph.local-{embed_model_name}")
async def graph_local(
        body : GraphRequest,
        logger: Logger,
        graph_service: GraphService = Depends(get_graph_service)
):
    logger.info(f"Handling graph request for {body.video_id}...")

    graph = graph_service.generate_graph(body.entity_relations)
    logger.info(f"Made a set of points for video {body.video_id}")

    result=GraphResult.from_graph(graph)

    await broker.publish(GraphResponse(
        job_id=body.job_id,
        result=result
    ), queue="graph.result")