from dataclasses import dataclass


@dataclass
class GraphNode:
    name: str
    pos_x: float
    pos_y: float

@dataclass
class GraphRelation:
    description: str
    source_node: GraphNode
    target_node: GraphNode

@dataclass
class Graph:
    nodes: list[GraphNode]
    relations: list[GraphRelation]