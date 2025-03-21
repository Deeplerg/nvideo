from datetime import datetime
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

class TranscriptionResult(BaseModel):
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
    content: str


class SummaryRequest(BaseModel):
    job_id: UUID
    video_id: str
    transcription: list[TranscriptionChunkResult]

class ChunkSummaryResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class SummaryResult(BaseModel):
    job_id: UUID
    result: list[ChunkSummaryResult]