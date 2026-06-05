# gcc
FROM python:3.12-slim

WORKDIR /app

RUN apt update && apt install -y libgomp1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./local_graph_service/requirements.torch.txt .
RUN uv pip install --system --no-cache -r requirements.torch.txt

COPY ./local_graph_service/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY ./local_graph_service/src/ ./local_graph_service/
COPY ./shared/ ./shared/

# ENV LD_LIBRARY_PATH=/usr/local/lib/python3.12/site-packages/nvidia/cudnn/lib/

CMD ["fastapi", "run", "/app/local_graph_service/main.py", "--port", "8000"]