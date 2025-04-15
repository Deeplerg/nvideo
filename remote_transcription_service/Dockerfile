# gcc
FROM python:3.12-slim

WORKDIR /app

RUN apt update
RUN apt install -y ffmpeg

COPY ./remote_transcription_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./remote_transcription_service/src/ ./remote_transcription_service/
COPY ./shared/ ./shared/

CMD ["fastapi", "run", "/app/remote_transcription_service/main.py", "--port", "8000"]