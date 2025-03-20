import os
from .AudioSplitter import split_audio
from .TranscriptionChunk import TranscriptionChunk
from .TransformerTranscriptionModel import TransformerTranscriptionModel


class TranscriptionService:
    def __init__(self, model: TransformerTranscriptionModel):
        self.model = model

    def transcribe(self, file_path, segment_length_ms) -> list[TranscriptionChunk]:
        transcription_chunks = []

        chunk_files = []

        for audio_chunk in split_audio(file_path, segment_length_ms, use_temp_dir=True):
            transcription = self.model.transcribe(audio_chunk.chunk_path)

            chunk = TranscriptionChunk(
                text=transcription,
                start_time_ms=audio_chunk.start_time_ms,
                end_time_ms=audio_chunk.end_time_ms
            )

            transcription_chunks.append(chunk)
            chunk_files.append(audio_chunk.chunk_path)

        self.__cleanup_files(chunk_files)
        return transcription_chunks

    def __cleanup_files(self, files: list[str]):
        for file_path in files:
            if os.path.exists(file_path):
                os.remove(file_path)