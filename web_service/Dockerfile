FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./web_service/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY ./web_service/src/ ./web_service/
COPY ./shared/ ./shared/

CMD ["uvicorn", "web_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips=*"]