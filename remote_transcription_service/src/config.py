import os

class AppConfiguration:
    __RMQ_USER: str = os.getenv("RABBITMQ_USER")
    __RMQ_PASS: str = os.getenv("RABBITMQ_PASS")
    __RMQ_PROTO: str = os.getenv("RABBITMQ_PROTO")
    __RMQ_HOST: str = os.getenv("RABBITMQ_HOST")
    __RMQ_PORT: str = os.getenv("RABBITMQ_PORT")
    AMQP_URL: str = f"{__RMQ_PROTO}://{__RMQ_USER}:{__RMQ_PASS}@{__RMQ_HOST}:{__RMQ_PORT}/"
    TRANSCRIPTION_PROVIDER: str = os.getenv("REMOTE_TRANSCRIPTION_PROVIDER")
    TRANSCRIPTION_CHUNK_SECONDS: int = int(os.getenv("TRANSCRIPTION_CHUNK_SECONDS"))
    DEEPGRAM_TRANSCRIPTION_MODEL: str = os.getenv("REMOTE_TRANSCRIPTION_DEEPGRAM_MODEL")
    DEEPGRAM_TRANSCRIPTION_API_KEY: str = os.getenv("REMOTE_TRANSCRIPTION_DEEPGRAM_API_KEY")
    GEMINI_TRANSCRIPTION_MODEL: str = os.getenv("REMOTE_TRANSCRIPTION_GEMINI_MODEL")
    GEMINI_TRANSCRIPTION_API_KEY: str = os.getenv("REMOTE_TRANSCRIPTION_GEMINI_API_KEY")
    GEMINI_TRANSCRIPTION_PROMPT: str = os.getenv("REMOTE_TRANSCRIPTION_GEMINI_PROMPT")