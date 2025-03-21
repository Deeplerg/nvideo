FROM python:3.13-alpine

WORKDIR /app

RUN apk add gcc python3-dev musl-dev linux-headers

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

CMD ["fastapi", "run", "/app/src/main.py", "--port", "8000"]