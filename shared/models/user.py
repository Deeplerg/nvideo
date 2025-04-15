from datetime import datetime
from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    role: str

class UpdateUserRoleRequest(BaseModel):
    role: str