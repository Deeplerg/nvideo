import os

class AppConfiguration:
    __RMQ_USER: str = os.getenv("RABBITMQ_USER")
    __RMQ_PASS: str = os.getenv("RABBITMQ_PASS")
    __RMQ_HOST: str = os.getenv("RABBITMQ_HOST")
    __RMQ_PORT: str = os.getenv("RABBITMQ_PORT")
    AMQP_URL: str = f"amqp://{__RMQ_USER}:{__RMQ_PASS}@{__RMQ_HOST}:{__RMQ_PORT}/"
    __API_PROTO: str = os.getenv("API_PROTO", "http")
    __API_HOST: str = os.getenv("API_HOST", "api")
    __API_PORT: str = os.getenv("API_PORT", "8000")
    __API_PATH: str = os.getenv("API_PATH", "")
    API_URL: str = f"{__API_PROTO}://{__API_HOST}:{__API_PORT}{__API_PATH}"
