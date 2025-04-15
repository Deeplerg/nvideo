from logging import Logger
from .EmbeddingService import EmbeddingService
from .Graph import *
from .PCAService import PCAService
from .TSNEService import TSNEService
from .UMAPService import UMAPService
from ..config import AppConfiguration
from shared.models import *


class GraphService:
    def __init__(self,
                 logger: Logger,
                 embed: EmbeddingService,
                 pca: PCAService,
                 tsne: TSNEService,
                 umap: UMAPService):
        self.__logger = logger
        self.__embed = embed
        self.__pca = pca
        self.__tsne = tsne
        self.__umap = umap

    def generate_graph(self, entity_relations: EntityRelationResult) -> Graph:
        entity_names = [entity.name for entity in entity_relations.entities]

        self.__logger.info("Generating embeddings")
        embeddings = self.__embed.embed(entity_names)

        if AppConfiguration.GRAPH_USE_PCA:
            self.__logger.info("Reducing dimensions with PCA")
            embeddings = self.__pca.reduce(embeddings)

        if AppConfiguration.GRAPH_FAVOR_UMAP and embeddings.shape[0] > 3:
            self.__logger.info("Reducing to 2D with UMAP")
            coords_2d = self.__umap.reduce(embeddings)
        else:
            self.__logger.info("Reducing to 2D with t-SNE")
            coords_2d = self.__tsne.reduce(embeddings)

        # dict (name, node) for later reference
        nodes = {}
        for i, entity in enumerate(entity_relations.entities):
            nodes[entity.name] = GraphNode(
                name=entity.name,
                pos_x=float(coords_2d[i][0]),
                pos_y=float(coords_2d[i][1])
            )

        relations = []
        for rel in entity_relations.relationships:
            relations.append(GraphRelation(
                description=rel.description,
                source_node=nodes[rel.source_entity],
                target_node=nodes[rel.target_entity]
            ))

        return Graph(nodes=list(nodes.values()), relations=relations)