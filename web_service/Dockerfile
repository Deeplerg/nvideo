FROM python:3.13-alpine

WORKDIR /app

COPY ./web_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./web_service/src/ ./web_service/
COPY ./shared/ ./shared/

CMD ["uvicorn", "web_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips=*"]