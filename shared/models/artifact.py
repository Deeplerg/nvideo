from typing import Any
from uuid import UUID
from pydantic import BaseModel

class ArtifactResponse(BaseModel):
    id: UUID
    job_id: UUID
    type: str
    content: Any