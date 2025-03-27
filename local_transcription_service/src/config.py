import os

class AppConfiguration:
    __RMQ_USER: str = os.getenv("RABBITMQ_USER")
    __RMQ_PASS: str = os.getenv("RABBITMQ_PASS")
    __RMQ_PROTO: str = os.getenv("RABBITMQ_PROTO")
    __RMQ_HOST: str = os.getenv("RABBITMQ_HOST")
    __RMQ_PORT: str = os.getenv("RABBITMQ_PORT")
    AMQP_URL: str = f"{__RMQ_PROTO}://{__RMQ_USER}:{__RMQ_PASS}@{__RMQ_HOST}:{__RMQ_PORT}/"
    TRANSCRIPTION_MODEL: str = os.getenv("TRANSCRIPTION_MODEL")
    TRANSCRIPTION_MODEL_DIR: str = os.getenv("TRANSCRIPTION_MODEL_DIR")
    TRANSCRIPTION_CHUNK_SECONDS: int = int(os.getenv("TRANSCRIPTION_CHUNK_SECONDS"))
    TRANSCRIPTION_LIBRARY: str = os.getenv("TRANSCRIPTION_LIBRARY")