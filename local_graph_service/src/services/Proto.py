import torch.cuda
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import plotly.graph_objects as go
import networkx as nx
import umap


entities = [
    "Google",
    "Android",
    "QPR",
    "Android 16 QPR 1",
    "Android 16.1",
    "Android 16",
    "патчи",
    "обновления",
    "Google Fitch Drop",
    "SMS"
]
relationships = [
    {"source": "Google", "target": "Android", "relation": "решили добавить версию"},
    {"source": "Android", "target": "QPR", "relation": "версия"},
    {"source": "QPR", "target": "Android", "relation": "вышел в первом квартале 2025 года"},
    {"source": "Android 16 QPR 1", "target": "Android", "relation": "версия"},
    {"source": "Android 16.1", "target": "Android", "relation": "версия"},
    {"source": "патчи", "target": "Android", "relation": "выходят ежемесячно"},
    {"source": "обновления", "target": "Android", "relation": "выходят"},
    {"source": "Android 16", "target": "обновления", "relation": "есть что посмотреть"},
    {"source": "Google Fitch Drop", "target": "SMS", "relation": "добавлена функция обнаружения мошенничества"}
]

print("Load")
device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(model_name, device=device)
print("Encode")
embeddings = model.encode(entities)
print("Encoded")

n_components_pca=min(50, embeddings.shape[0], embeddings.shape[1])
pca = PCA(n_components=n_components_pca)
print("PCA")
embeddings_pca = pca.fit_transform(embeddings)
print("PCA'd")

umap = umap.UMAP(n_components=2, n_neighbors=2)
print("UMAP")
#umap = umap.UMAP(n_components=2)
embeddings_2d = umap.fit_transform(embeddings_pca)
# print("round 2")
# embeddings_2d = umap.fit_transform(embeddings)
print("UMAP'd")

# print("TSNE")
# tsne = TSNE(n_components=2, perplexity=2, init='pca')
# embeddings_2d = tsne.fit_transform(embeddings_pca)
# print("TSNE'd")

G = nx.Graph()

for i, entity in enumerate(entities):
    G.add_node(entity, pos=embeddings_2d[i])

for rel in relationships:
    G.add_edge(rel["source"], rel["target"], label=rel["relation"])

pos = nx.get_node_attributes(G, 'pos')

edge_trace = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_trace.append(go.Scatter(
        x=[x0, x1, None], y=[y0, y1, None],
        line=dict(width=1, color='gray'),
        hoverinfo='none',
        mode='lines'))

node_trace = go.Scatter(
    x=[], y=[], text=[], mode='markers+text', textposition="top center",
    hoverinfo='text', marker=dict(
        showscale=False,
        colorscale='YlGnBu',
        size=20,
        color='lightblue',
        line=dict(width=2, color='black'))
)

for node in G.nodes():
    x, y = pos[node]
    node_trace['x'] += (x,)
    node_trace['y'] += (y,)
    node_trace['text'] += (node,)

fig = go.Figure(data=edge_trace + [node_trace],
                layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    title="Визуализация сущностей и связей"
                ))

fig.write_html("plotly_graph.html")
