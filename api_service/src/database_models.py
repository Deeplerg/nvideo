from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Job(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: str
    video_id: str
    status: str = "created"
    user_id: int = Field(default=None, foreign_key="user.id")
    action_models: list[str] = Field(default=[], sa_column=Column(JSON))

class JobArtifact(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    job_id: UUID = Field(default=None, foreign_key="job.id")
    type: str
    content: str

class AvailableModel(SQLModel, table=True):
    name: str = Field(primary_key=True)
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))