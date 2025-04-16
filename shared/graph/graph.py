from dataclasses import dataclass
from shared.models import *


@dataclass
class GraphNode:
    name: str
    pos_x: float
    pos_y: float

    def to_result(self):
        return GraphNodeResult(
            name=self.name,
            pos_x=self.pos_x,
            pos_y=self.pos_y
        )

@dataclass
class GraphRelation:
    description: str
    source_node: GraphNode
    target_node: GraphNode

    def to_result(self):
        return GraphRelationResult(
            description=self.description,
            source_node=self.source_node.name,
            target_node=self.target_node.name
        )


@dataclass
class Graph:
    nodes: list[GraphNode]
    relations: list[GraphRelation]

    def to_result(self):
        return GraphResult(
            nodes=[
                node.to_result()
                for node in self.nodes
            ],
            relations=[
                relation.to_result()
                for relation in self.relations
            ]
        )