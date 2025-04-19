from uuid import UUID
from pydantic import BaseModel
from .transcription import TranscriptionChunkResult

class SummaryRequest(BaseModel):
    job_id: UUID
    video_id: str
    transcription: list[TranscriptionChunkResult]

class ChunkSummaryResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class SummaryResult(BaseModel):
    chunks: list[ChunkSummaryResult]
    overall_summary: str | None

class SummaryResponse(BaseModel):
    job_id: UUID
    result: SummaryResult