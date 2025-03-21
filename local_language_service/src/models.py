from uuid import UUID

from pydantic import BaseModel

class TranscriptionChunkResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class TranscriptionResult(BaseModel):
    job_id: UUID
    result: list[TranscriptionChunkResult]


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


class ModelAvailable(BaseModel):
    model_name: str