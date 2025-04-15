FROM python:3.13-alpine

WORKDIR /app

COPY ./api_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./api_service/src/ ./api_service/
COPY ./shared/ ./shared/

CMD ["uvicorn", "api_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips=*"]