from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class CreateJobRequest(BaseModel):
    type: str
    video_id: str
    action_models: list[str]
    user_id: int

class JobResponse(BaseModel):
    id: UUID
    type: str
    video_id: str
    status: str
    user_id: int

class JobCompleted(BaseModel):
    id: UUID
    type: str
    video_id: str
    user_id: int

class JobStatusUpdated(BaseModel):
    id: UUID
    video_id: str
    status: str
    user_id: int


class CreateUserRequest(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: int
    username: str


class TranscriptionRequest(BaseModel):
    job_id: UUID
    video_id: str

class TranscriptionChunkResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class TranscriptionResponse(BaseModel):
    job_id: UUID
    result: list[TranscriptionChunkResult]


class ModelAvailable(BaseModel):
    model_name: str

class AvailableModelResponse(BaseModel):
    name: str
    last_seen: datetime


class ArtifactResponse(BaseModel):
    id: UUID
    job_id: UUID
    type: str
    content: Any


class SummaryRequest(BaseModel):
    job_id: UUID
    video_id: str
    transcription: list[TranscriptionChunkResult]

class ChunkSummaryResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class SummaryResponse(BaseModel):
    job_id: UUID
    result: list[ChunkSummaryResult]


class EntityRelationRequest(BaseModel):
    job_id: UUID
    video_id: str
    transcription: list[TranscriptionChunkResult]

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

class EntityRelationResponse(BaseModel):
    job_id: UUID
    result: EntityRelationResult


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