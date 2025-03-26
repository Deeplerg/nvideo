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