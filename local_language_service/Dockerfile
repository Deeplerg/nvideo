FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./local_language_service/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY ./local_language_service/src/ ./local_language_service/
COPY ./shared/ ./shared/

CMD ["fastapi", "run", "/app/local_language_service/main.py", "--port", "8000"]