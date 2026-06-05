from pydantic import BaseModel, Field

class TopicSchema(BaseModel):
    title: str = Field(description="Short, catchy title for this segment")
    start_time_ms: int = Field(description="Exact start time in milliseconds")
    end_time_ms: int = Field(description="Exact end time in milliseconds")
    summary: str = Field(description="Detailed summary of what is discussed")
    tags: list[str] = Field(description="Specific tags or keywords (e.g., 'Bitcoin', 'Investment')")
    virality_score: int = Field(description="Viral potential score from 1 to 100")
    virality_reasoning: str = Field(description="Reasoning for the given virality score")

class TopicExtractionSchema(BaseModel):
    topics: list[TopicSchema]

class MacroTagMappingSchema(BaseModel):
    mapping: dict[str, str] = Field(description="Mapping of original tags to their macro-categories")