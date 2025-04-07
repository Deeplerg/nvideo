from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel

class AvailableModelResponse(BaseModel):
    name: str
    last_seen: datetime

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    role: str

class UpdateUserRoleRequest(BaseModel):
    role: str

class JobResponse(BaseModel):
    id: UUID
    type: str
    video_id: str
    status: str
    user_id: int

class ArtifactResponse(BaseModel):
    id: UUID
    job_id: UUID
    type: str
    content: Any

class TranscriptionChunkResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class ChunkSummaryResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

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

class JobStatusUpdated(BaseModel):
    id: UUID
    video_id: str
    status: str
    user_id: int

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