from logging import Logger
from numpy import ndarray
from shared.models import *
from .embedding_model import EmbeddingModel
from .graph import Graph, GraphNode, GraphRelation
from .pca_service import PCAService
from .tsne_service import TSNEService
from .umap_service import UMAPService


class GraphService:
    def __init__(self,
                 logger: Logger,
                 embed: EmbeddingModel,
                 pca: PCAService,
                 tsne: TSNEService,
                 umap: UMAPService,
                 use_pca: bool,
                 favor_umap: bool,
                 external_reduction: bool):
        self.__logger = logger
        self.__embed = embed
        self.__pca = pca
        self.__tsne = tsne
        self.__umap = umap
        self.__use_pca = use_pca
        self.__favor_umap = favor_umap
        self.__external_reduction = external_reduction

    def generate_graph(self, entity_relations: EntityRelationResult) -> Graph:
        entity_names = [entity.name for entity in entity_relations.entities]

        self.__logger.info("Generating embeddings")
        embeddings: ndarray = self.__embed.embed(entity_names)

        coords_2d: ndarray = embeddings
        if not self.__external_reduction:
            coords_2d = self.__reduce(embeddings)

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

    def __reduce(self, embeddings: ndarray) -> ndarray:
        if self.__use_pca:
            self.__logger.info("Reducing dimensions with PCA")
            embeddings = self.__pca.reduce(embeddings)

        if self.__favor_umap and embeddings.shape[0] > 3:
            self.__logger.info("Reducing to 2D with UMAP")
            coords_2d = self.__umap.reduce(embeddings)
        else:
            self.__logger.info("Reducing to 2D with t-SNE")
            coords_2d = self.__tsne.reduce(embeddings)

        return coords_2d