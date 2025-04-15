from uuid import UUID
from pydantic import BaseModel
from .entity_relation import EntityRelationResult

class GraphNodeResult(BaseModel):
    name: str
    pos_x: float
    pos_y: float

class GraphRelationResult(BaseModel):
    description: str
    source_node: str
    target_node: str

class GraphResult(BaseModel):
    nodes: list[GraphNodeResult]
    relations: list[GraphRelationResult]

class GraphRequest(BaseModel):
    job_id: UUID
    video_id: str
    entity_relations: EntityRelationResult

class GraphResponse(BaseModel):
    job_id: UUID
    result: GraphResult