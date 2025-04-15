from pydantic import BaseModel
from shared.models import *


class Entity(BaseModel):
    name: str
    chunk_start_time_ms: int
    chunk_end_time_ms: int

    def to_result(self):
        return EntityResult(
            name=self.name,
            chunk_start_time_ms=self.chunk_start_time_ms,
            chunk_end_time_ms=self.chunk_end_time_ms
        )

class Relationship(BaseModel):
    source_entity: str
    target_entity: str
    relation_description: str
    chunk_start_time_ms: int
    chunk_end_time_ms: int

    def to_result(self):
        return RelationshipResult(
            source_entity=self.source_entity,
            target_entity=self.target_entity,
            description=self.relation_description,
            chunk_start_time_ms=self.chunk_start_time_ms,
            chunk_end_time_ms=self.chunk_end_time_ms
        )

class EntityRelations(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]

    def to_result(self):
        return EntityRelationResult(
            entities=[
                entity.to_result()
                for entity in self.entities
            ],
            relationships=[
                relationship.to_result()
                for relationship in self.relationships
            ]
        )


class EntitySchema(BaseModel):
    name: str

class RelationshipSchema(BaseModel):
    source_entity: str
    target_entity: str
    relation_description: str

class EntityRelationsSchema(BaseModel):
    new_entities: list[EntitySchema]
    new_relationships: list[RelationshipSchema]