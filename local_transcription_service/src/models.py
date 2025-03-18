from uuid import UUID

from pydantic import BaseModel

class TranscriptionRequest(BaseModel):
    job_id: UUID
    video_id: str

class TranscriptionResult(BaseModel):
    job_id: UUID
    result: str

class ModelAvailable(BaseModel):
    model_name: str