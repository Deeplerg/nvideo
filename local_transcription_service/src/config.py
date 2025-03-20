import os

class AppConfiguration:
    AMQP_URL: str = os.getenv("AMQP_URL")
    TRANSCRIPTION_MODEL: str = os.getenv("TRANSCRIPTION_MODEL")
    TRANSCRIPTION_MODEL_DIR: str = os.getenv("TRANSCRIPTION_MODEL_DIR")