import os
from . import TranscriptionModel, TranscriptionChunk
from ..audio import split_audio


class TranscriptionService:
    def __init__(self, model: TranscriptionModel):
        self.model = model

    async def transcribe(self, file_path, segment_length_ms) -> list[TranscriptionChunk]:
        transcription_chunks = []

        async for audio_chunk in split_audio(file_path, segment_length_ms, use_temp_dir=True):
            transcription = await self.model.transcribe(audio_chunk.chunk_path)

            chunk = TranscriptionChunk(
                text=transcription,
                start_time_ms=audio_chunk.start_time_ms,
                end_time_ms=audio_chunk.end_time_ms
            )

            transcription_chunks.append(chunk)

            if os.path.exists(audio_chunk.chunk_path):
                os.remove(audio_chunk.chunk_path)

        return transcription_chunks