from datetime import datetime
from pydantic import BaseModel

class ModelAvailable(BaseModel):
    model_name: str

class AvailableModelResponse(BaseModel):
    name: str
    last_seen: datetime
