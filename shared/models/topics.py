from enum import Enum
from pydantic import BaseModel
from uuid import UUID
from .transcription import TranscriptionChunkResult

class PostType(str, Enum):
    POST = "post"
    TIKTOK_SCENARIO = "tiktok_scenario"

class TopicResult(BaseModel):
    title: str
    start_time_ms: int
    end_time_ms: int
    summary: str
    tags: list[str]
    virality_score: int
    virality_reasoning: str

class TopicsExtractionResult(BaseModel):
    topics: list[TopicResult]
    macro_tags_mapping: dict[str, str]

class GeneratePostRequest(BaseModel):
    topic_start_ms: int
    topic_end_ms: int
    post_type: PostType

class TopicsRequest(BaseModel):
    job_id: UUID
    video_id: str
    transcription: list[TranscriptionChunkResult]

class TopicsResponse(BaseModel):
    job_id: UUID
    result: TopicsExtractionResult

class GeneratePostRpcRequest(BaseModel):
    transcript_slice: str
    post_type: PostType