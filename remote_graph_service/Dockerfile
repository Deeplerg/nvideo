# gcc
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./remote_graph_service/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY ./remote_graph_service/src/ ./remote_graph_service/
COPY ./shared/ ./shared/

CMD ["fastapi", "run", "/app/remote_graph_service/main.py", "--port", "8000"]