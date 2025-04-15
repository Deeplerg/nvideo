# gcc
FROM python:3.12-slim

WORKDIR /app

COPY ./local_graph_service/requirements.torch.txt .
RUN pip install --no-cache-dir -r requirements.torch.txt

RUN apt update
RUN apt install -y ffmpeg

COPY ./local_graph_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./local_graph_service/src/ ./local_graph_service/
COPY ./shared/ ./shared/

ENV LD_LIBRARY_PATH=/usr/local/lib/python3.12/site-packages/nvidia/cudnn/lib/

CMD ["fastapi", "run", "/app/local_graph_service/main.py", "--port", "8000"]