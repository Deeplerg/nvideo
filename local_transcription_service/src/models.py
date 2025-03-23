from uuid import UUID

from pydantic import BaseModel

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