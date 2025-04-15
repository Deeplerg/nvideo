from uuid import UUID
from pydantic import BaseModel
from .transcription import TranscriptionChunkResult

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