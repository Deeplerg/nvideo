import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio
from typing import List, Tuple, Set, Dict
import logging
from shared.models import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphService:

    def __filter_entities_relations(
        self,
        entity_relation_data: EntityRelationResult,
        max_end_time_ms: int
    ) -> Tuple[List[EntityResult], List[RelationshipResult]]:
        """Filters entities and relations based on chunk start time."""
        filtered_entities = [
            e for e in entity_relation_data.entities
            if e.chunk_start_time_ms < max_end_time_ms
        ]
        filtered_relations = [
            r for r in entity_relation_data.relationships
            if r.chunk_start_time_ms < max_end_time_ms
        ]
        return filtered_entities, filtered_relations

    def create_cumulative_graph_html(
        self,
        graph_data: GraphResult,
        entity_relation_data: EntityRelationResult,
        chunk_end_time_ms: int
    ) -> str:

        filtered_chunk_entities, filtered_chunk_relations = self.__filter_entities_relations(
            entity_relation_data, chunk_end_time_ms
        )

        present_entity_names: Set[str] = {e.name for e in filtered_chunk_entities}

        nodes_to_display = [
            node for node in graph_data.nodes if node.name in present_entity_names
        ]
        node_positions: Dict[str, Tuple[float, float]] = {
            node.name: (node.pos_x, node.pos_y) for node in nodes_to_display
        }

        relations_to_display = []
        relation_keys_in_chunk = {
             (r.source_entity, r.target_entity, r.description) for r in filtered_chunk_relations
        }

        for rel in graph_data.relations:
            source_exists = rel.source_node in node_positions
            target_exists = rel.target_node in node_positions
            relation_appeared = (rel.source_node, rel.target_node, rel.description) in relation_keys_in_chunk
            if source_exists and target_exists and relation_appeared:
                relations_to_display.append(rel)

        if not nodes_to_display:
             return "<p>Нет данных для отображения для этого временного интервала.</p>"

        G = nx.DiGraph()
        for node in nodes_to_display: G.add_node(node.name)
        for rel in relations_to_display: G.add_edge(rel.source_node, rel.target_node, label=rel.description)

        edge_x, edge_y, edge_labels, edge_mid_x, edge_mid_y = [], [], [], [], []
        for edge in G.edges(data=True):
            try:
                x0, y0 = node_positions[edge[0]]
                x1, y1 = node_positions[edge[1]]
                edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])
                edge_mid_x.append((x0 + x1) / 2); edge_mid_y.append((y0 + y1) / 2)
                edge_labels.append(edge[2].get('label', ''))
            except KeyError as e:
                logger.error(f"Graph generation: Node position key error for edge {edge}: {e}. Skipping edge.")
                continue

        edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='#888'), hoverinfo='none', mode='lines')
        node_trace = go.Scatter(
            x=[node_positions[node][0] for node in G.nodes()],
            y=[node_positions[node][1] for node in G.nodes()],
            mode='markers+text', hoverinfo='text',
            text=[node for node in G.nodes()], textposition="top center",
            marker=dict(showscale=False, colorscale='YlGnBu', reversescale=True, color=[], size=15, line_width=2)
        )
        annotations = [
            dict(x=edge_mid_x[i], y=edge_mid_y[i], xref='x', yref='y', text=label, showarrow=False, font=dict(size=9, color="#555"))
            for i, label in enumerate(edge_labels) if label
        ]

        layout = go.Layout(
            height=500,
            showlegend=False, hovermode='closest',
            margin=dict(b=5,l=5,r=5,t=5),
            annotations=annotations,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        fig = go.Figure(data=[edge_trace, node_trace], layout=layout)

        graph_html = pio.to_html(
            fig,
            full_html=False,
            include_plotlyjs=False
        )
        return graph_html