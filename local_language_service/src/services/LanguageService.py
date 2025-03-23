import json
from dataclasses import dataclass
from logging import Logger

from ollama import ChatResponse, AsyncClient

from .EntityRelations import EntityRelations, Entity, Relationship, EntityRelationsSchema
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
            logger: Logger):
        self.__client = client
        self.__logger = logger
        self.__model_name = AppConfiguration.LANGUAGE_MODEL
        self.__summary_system_prompt = AppConfiguration.LANGUAGE_SUMMARY_SYSTEM_PROMPT
        self.__entity_system_prompt = AppConfiguration.LANGUAGE_ENTITY_SYSTEM_PROMPT

    async def summarize(self, chunks: list[TranscriptionChunkResult]) -> list[ChunkSummaryResponse]:
        summaries: list[ChunkSummaryResponse] = []

        for chunk in chunks:
            threshold = AppConfiguration.LANGUAGE_EMPTY_CHUNK_THRESHOLD_MS
            if chunk.end_time_ms - chunk.start_time_ms < threshold:
                continue

            summary = await self.__summarize_chunk(chunk)
            summaries.append(ChunkSummaryResponse(
                text=summary,
                start_time_ms=chunk.start_time_ms,
                end_time_ms=chunk.end_time_ms
            ))
            self.__logger.info(
                f"Summarized chunk at {chunk.start_time_ms}, summary length: {len(summary)}")

        return summaries

    async def generate_entity_relations(self, chunks: list[TranscriptionChunkResult]) -> EntityRelations:
        entities: list[Entity] = []
        relationships: list[Relationship] = []
        entity_names_set = set()

        for chunk in chunks:
            threshold = AppConfiguration.LANGUAGE_EMPTY_CHUNK_THRESHOLD_MS
            if chunk.end_time_ms - chunk.start_time_ms < threshold:
                continue

            entity_relations_chunk = await self.__extract_entity_relations_chunk(
                chunk=chunk,
                existing_entity_relations=EntityRelations(
                    entities=entities,
                    relationships=relationships
                )
            )

            new_entities = []
            for entity in entity_relations_chunk.entities:
                if entity.name not in entity_names_set:
                    entity_names_set.add(entity.name)
                    new_entities.append(entity)

            entities.extend(new_entities)
            relationships.extend(entity_relations_chunk.relationships)

            self.__logger.info(
                f"Extracted {len(entity_relations_chunk.entities)} entities and "
                f"{len(entity_relations_chunk.relationships)} relationships from "
                f"chunk at {chunk.start_time_ms}"
            )

            for rel in relationships:
                entity_name: str | None = None
                if rel.source_entity not in entity_names_set:
                    entity_name = rel.source_entity
                if rel.target_entity not in entity_names_set:
                    entity_name = rel.target_entity

                if entity_name is None:
                    continue

                entity = Entity(
                    name=entity_name,
                    chunk_start_time_ms=chunk.start_time_ms,
                    chunk_end_time_ms=chunk.end_time_ms
                )
                entity_names_set.add(entity.name)
                entities.append(entity)

        return EntityRelations(entities=entities, relationships=relationships)

    def __ms_to_minutes_seconds(self, ms) -> str:
        seconds = ms // 1000
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

    async def __summarize_chunk(self, chunk : TranscriptionChunkResult) -> str:
        start_minutes_seconds = self.__ms_to_minutes_seconds(chunk.start_time_ms)
        end_minutes_seconds = self.__ms_to_minutes_seconds(chunk.end_time_ms)

        message = f"[Chunk {start_minutes_seconds} - {end_minutes_seconds}]\n{chunk.text}"

        response: ChatResponse = await self.__client.chat(
            model=self.__model_name,
            messages=[
                {"role": "system", "content": self.__summary_system_prompt},
                {"role": "user", "content": message}
            ],
            stream=False
        )
        return response.message.content

    async def __extract_entity_relations_chunk(
            self,
            chunk: TranscriptionChunkResult,
            existing_entity_relations: EntityRelations
    ) -> EntityRelations:
        start_minutes_seconds = self.__ms_to_minutes_seconds(chunk.start_time_ms)
        end_minutes_seconds = self.__ms_to_minutes_seconds(chunk.end_time_ms)

        existing_entity_relations_json = existing_entity_relations.model_dump_json(indent=2)
        existing_entity_relations_prompt = f"[Existing entities and relations]\n{existing_entity_relations_json}"
        transcript_prompt = f"[Chunk {start_minutes_seconds} - {end_minutes_seconds}]\n{chunk.text}"
        schema = EntityRelationsSchema.model_json_schema()

        response: ChatResponse = await self.__client.chat(
            model=self.__model_name,
            messages=[
                {"role": "system", "content": self.__entity_system_prompt},
                {"role": "user", "content": existing_entity_relations_prompt},
                {"role": "user", "content": transcript_prompt}
            ],
            stream=False,
            format=schema
        )

        self.__logger.info(response.message.content)

        result: dict = json.loads(response.message.content)

        entities = [
            Entity(
                name=entity["name"],
                chunk_start_time_ms=chunk.start_time_ms,
                chunk_end_time_ms=chunk.end_time_ms
            )
            for entity in result.get("new_entities", [])
        ]

        relationships = [
            Relationship(
                source_entity=rel["source_entity"],
                target_entity=rel["target_entity"],
                relation_description=rel["relation_description"],
                chunk_start_time_ms=chunk.start_time_ms,
                chunk_end_time_ms=chunk.end_time_ms
            )
            for rel in result.get("new_relationships", [])
        ]

        return EntityRelations(
            entities=entities,
            relationships=relationships
        )