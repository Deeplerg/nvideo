from uuid import UUID
from pydantic import BaseModel
from .services.EntityRelations import Entity, Relationship, EntityRelations


class TranscriptionChunkResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class TranscriptionResult(BaseModel):
    job_id: UUID
    result: list[TranscriptionChunkResult]


class SummaryRequest(BaseModel):
    job_id: UUID
    video_id: str
    transcription: list[TranscriptionChunkResult]

class ChunkSummaryResult(BaseModel):
    text: str
    start_time_ms: int
    end_time_ms: int

class SummaryResult(BaseModel):
    job_id: UUID
    result: list[ChunkSummaryResult]


class EntityRelationRequest(BaseModel):
    job_id: UUID
    video_id: str
    transcription: list[TranscriptionChunkResult]

class EntityResult(BaseModel):
    name: str
    chunk_start_time_ms: int
    chunk_end_time_ms: int

    def from_entity(entity: Entity):
        return EntityResult(
            name=entity.name,
            chunk_start_time_ms=entity.chunk_start_time_ms,
            chunk_end_time_ms=entity.chunk_end_time_ms
        )

class RelationshipResult(BaseModel):
    source_entity: str
    target_entity: str
    description: str
    chunk_start_time_ms: int
    chunk_end_time_ms: int

    def from_relationship(relationship: Relationship):
        return RelationshipResult(
            source_entity=relationship.source_entity,
            target_entity=relationship.target_entity,
            description=relationship.relation_description,
            chunk_start_time_ms=relationship.chunk_start_time_ms,
            chunk_end_time_ms=relationship.chunk_end_time_ms
        )

class EntityRelationResult(BaseModel):
    entities: list[EntityResult]
    relationships: list[RelationshipResult]

    def from_entity_relations(entity_relations: EntityRelations):
        return EntityRelationResult(
            entities=[
                EntityResult.from_entity(entity)
                for entity in entity_relations.entities
            ],
            relationships=[
                RelationshipResult.from_relationship(relationship)
                for relationship in entity_relations.relationships
            ]
        )

class EntityRelationResponse(BaseModel):
    job_id: UUID
    result: EntityRelationResult


class ModelAvailable(BaseModel):
    model_name: str