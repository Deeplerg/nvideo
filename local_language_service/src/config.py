import os

class AppConfiguration:
    AMQP_URL: str = os.getenv("AMQP_URL")
    LANGUAGE_SUMMARY_SYSTEM_PROMPT: str = os.getenv("LANGUAGE_SUMMARY_SYSTEM_PROMPT")
    LANGUAGE_MODEL : str = os.getenv("LANGUAGE_MODEL")
    OLLAMA_PORT : int = int(os.getenv("OLLAMA_PORT"))
    OLLAMA_HOST : str = os.getenv("OLLAMA_HOST")