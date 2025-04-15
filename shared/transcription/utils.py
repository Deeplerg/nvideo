from . import TranscriptionChunk
from ..models import TranscriptionChunkResult

def convert_to_chunk_results(chunks: list[TranscriptionChunk]) -> list[TranscriptionChunkResult]:
    return [
        TranscriptionChunkResult(
            text=chunk.text,
            start_time_ms=chunk.start_time_ms,
            end_time_ms=chunk.end_time_ms
        )
        for chunk in chunks
    ]