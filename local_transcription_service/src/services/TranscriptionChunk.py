from dataclasses import dataclass

@dataclass
class TranscriptionChunk:
    text: str
    start_time_ms: int
    end_time_ms: int