import os

class AppConfiguration:
    __RMQ_USER: str = os.getenv("RABBITMQ_USER")
    __RMQ_PASS: str = os.getenv("RABBITMQ_PASS")
    __RMQ_PROTO: str = os.getenv("RABBITMQ_PROTO")
    __RMQ_HOST: str = os.getenv("RABBITMQ_HOST")
    __RMQ_PORT: str = os.getenv("RABBITMQ_PORT")
    AMQP_URL: str = f"{__RMQ_PROTO}://{__RMQ_USER}:{__RMQ_PASS}@{__RMQ_HOST}:{__RMQ_PORT}/"
    LANGUAGE_SUMMARY_SYSTEM_PROMPT: str = os.getenv("LANGUAGE_SUMMARY_SYSTEM_PROMPT")
    LANGUAGE_OVERALL_SUMMARY_SYSTEM_PROMPT: str = os.getenv("LANGUAGE_OVERALL_SUMMARY_SYSTEM_PROMPT")
    LANGUAGE_ENTITY_SYSTEM_PROMPT: str = os.getenv("LANGUAGE_ENTITY_SYSTEM_PROMPT")
    LANGUAGE_MODEL : str = os.getenv("LOCAL_LANGUAGE_MODEL")
    OLLAMA_PORT : int = int(os.getenv("OLLAMA_PORT"))
    OLLAMA_HOST : str = os.getenv("OLLAMA_HOST")
    LANGUAGE_EMPTY_CHUNK_THRESHOLD_MS: int = int(os.getenv("LANGUAGE_EMPTY_CHUNK_THRESHOLD_MS", "1000"))