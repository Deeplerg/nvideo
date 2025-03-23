from pydantic import BaseModel


class Entity(BaseModel):
    name: str
    chunk_start_time_ms: int
    chunk_end_time_ms: int

class Relationship(BaseModel):
    source_entity: str
    target_entity: str
    relation_description: str
    chunk_start_time_ms: int
    chunk_end_time_ms: int

class EntityRelations(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]


class EntitySchema(BaseModel):
    name: str

class RelationshipSchema(BaseModel):
    source_entity: str
    target_entity: str
    relation_description: str

class EntityRelationsSchema(BaseModel):
    new_entities: list[EntitySchema]
    new_relationships: list[RelationshipSchema]