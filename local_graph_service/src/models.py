from uuid import UUID
from pydantic import BaseModel
from .services.Graph import Graph, GraphNode, GraphRelation


class TranscriptionChunkResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class TranscriptionResponse(BaseModel):
    job_id: UUID
    result: list[TranscriptionChunkResult]


class ChunkSummaryResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class SummaryResponse(BaseModel):
    job_id: UUID
    result: list[ChunkSummaryResult]


class EntityResult(BaseModel):
    name: str
    chunk_start_time_ms: int
    chunk_end_time_ms: int

class RelationshipResult(BaseModel):
    source_entity: str
    target_entity: str
    description: str
    chunk_start_time_ms: int
    chunk_end_time_ms: int

class EntityRelationResult(BaseModel):
    entities: list[EntityResult]
    relationships: list[RelationshipResult]


class GraphNodeResult(BaseModel):
    name: str
    pos_x: float
    pos_y: float

    def from_graph_node(graph_node: GraphNode):
        return GraphNodeResult(
            name=graph_node.name,
            pos_x=graph_node.pos_x,
            pos_y=graph_node.pos_y
        )

class GraphRelationResult(BaseModel):
    description: str
    source_node: str
    target_node: str

    def from_graph_relation(rel: GraphRelation):
        return GraphRelationResult(
            description=rel.description,
            source_node=rel.source_node.name,
            target_node=rel.target_node.name
        )

class GraphResult(BaseModel):
    nodes: list[GraphNodeResult]
    relations: list[GraphRelationResult]

    def from_graph(graph: Graph):
        return GraphResult(
            nodes=[
                GraphNodeResult.from_graph_node(node)
                for node in graph.nodes
            ],
            relations=[
                GraphRelationResult.from_graph_relation(relation)
                for relation in graph.relations
            ]
        )

class GraphRequest(BaseModel):
    job_id: UUID
    video_id: str
    entity_relations: EntityRelationResult

class GraphResponse(BaseModel):
    job_id: UUID
    result: GraphResult


class ModelAvailable(BaseModel):
    model_name: str