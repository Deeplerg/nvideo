FROM python:3.13-alpine

WORKDIR /app

RUN apk add gcc python3-dev musl-dev linux-headers

COPY ./remote_language_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./remote_language_service/src/ ./remote_language_service/
COPY ./shared/ ./shared/

CMD ["fastapi", "run", "/app/remote_language_service/main.py", "--port", "8000"]