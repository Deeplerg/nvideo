# gcc
FROM python:3.12-slim

WORKDIR /app

COPY ./remote_graph_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./remote_graph_service/src/ ./remote_graph_service/
COPY ./shared/ ./shared/

CMD ["fastapi", "run", "/app/remote_graph_service/main.py", "--port", "8000"]