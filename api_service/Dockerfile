FROM python:3.13-alpine

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./api_service/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY ./api_service/src/ ./api_service/
COPY ./shared/ ./shared/

CMD ["uvicorn", "api_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips=*"]