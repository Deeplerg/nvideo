# gcc
FROM python:3.12-slim

WORKDIR /app

COPY requirements.torch.txt .
RUN pip install --no-cache-dir -r requirements.torch.txt

RUN apt update
RUN apt install -y ffmpeg

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

ENV LD_LIBRARY_PATH=/usr/local/lib/python3.12/site-packages/nvidia/cudnn/lib/

CMD ["fastapi", "run", "/app/src/main.py", "--port", "8000"]