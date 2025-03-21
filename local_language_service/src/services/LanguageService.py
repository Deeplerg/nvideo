from dataclasses import dataclass
from logging import Logger

from ollama import ChatResponse, AsyncClient

from ..config import AppConfiguration
from ..models import TranscriptionChunkResult

@dataclass
class ChunkSummaryResponse:
    text: str
    start_time_ms: int
    end_time_ms: int

class LanguageService:
    def __init__(
            self,
            client: AsyncClient,
            logger: Logger,
            model_name: str,
            system_prompt: str):
        self.__client = client
        self.__logger = logger
        self.__model_name = model_name
        self.__system_prompt = system_prompt

    async def summarize(self, chunks: list[TranscriptionChunkResult]) -> list[ChunkSummaryResponse]:
        summaries: list[ChunkSummaryResponse] = []

        for chunk in chunks:
            summary = await self.__summarize_chunk(chunk)
            summaries.append(ChunkSummaryResponse(
                text=summary,
                start_time_ms=chunk.start_time_ms,
                end_time_ms=chunk.end_time_ms
            ))
            self.__logger.info(
                f"Summarized chunk at {chunk.start_time_ms}, summary length: {len(summary)}")

        return summaries

    def __ms_to_minutes_seconds(self, ms) -> str:
        seconds = ms // 1000
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

    async def __summarize_chunk(self, chunk : TranscriptionChunkResult) -> str:
        start_minutes_seconds = self.__ms_to_minutes_seconds(chunk.start_time_ms)
        end_minutes_seconds = self.__ms_to_minutes_seconds(chunk.end_time_ms)
        message = f"[Chunk {start_minutes_seconds} - {end_minutes_seconds}]\n" + chunk.text

        response : ChatResponse = await self.__client.chat(model=self.__model_name,
                                              messages=[
                                                  {"role": "system", "content": self.__system_prompt},
                                                  {"role": "user", "content": message}
                                              ],
                                              stream=False)
        return response.message.content
