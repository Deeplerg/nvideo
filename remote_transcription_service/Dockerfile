# gcc
FROM python:3.12-slim

WORKDIR /app

RUN apt update && apt install -y ffmpeg

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./remote_transcription_service/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY ./remote_transcription_service/src/ ./remote_transcription_service/
COPY ./shared/ ./shared/

CMD ["fastapi", "run", "/app/remote_transcription_service/main.py", "--port", "8000"]