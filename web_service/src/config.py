import os

class AppConfiguration:
    AMQP_URL: str = os.getenv("AMQP_URL")
    API_URL: str = os.getenv("API_URL")