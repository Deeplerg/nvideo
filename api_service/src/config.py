import os

class AppConfiguration:
    __RMQ_USER: str = os.getenv("RABBITMQ_USER")
    __RMQ_PASS: str = os.getenv("RABBITMQ_PASS")
    __RMQ_PROTO: str = os.getenv("RABBITMQ_PROTO")
    __RMQ_HOST: str = os.getenv("RABBITMQ_HOST")
    __RMQ_PORT: str = os.getenv("RABBITMQ_PORT")
    AMQP_URL: str = f"{__RMQ_PROTO}://{__RMQ_USER}:{__RMQ_PASS}@{__RMQ_HOST}:{__RMQ_PORT}/"
    __DB_USER: str = os.getenv("POSTGRES_USER")
    __DB_PASS: str = os.getenv("POSTGRES_PASSWORD")
    __DB_HOST: str = os.getenv("POSTGRES_HOST")
    __DB_PORT: str = os.getenv("POSTGRES_PORT")
    __DB_NAME: str = os.getenv("POSTGRES_DB")
    DATABASE_URL = f"postgresql+psycopg://{__DB_USER}:{__DB_PASS}@{__DB_HOST}:{__DB_PORT}/{__DB_NAME}"
    MODEL_THRESHOLD: int = int(os.getenv("MODEL_AVAILABILITY_THRESHOLD", "30"))
    ROOT_PATH: str = os.getenv("API_PATH", "/")
    ADMIN_USER: str | None = os.getenv("API_ADMIN_USER")