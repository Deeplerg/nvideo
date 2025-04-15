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