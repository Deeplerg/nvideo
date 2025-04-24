import asyncio
from logging import Logger
from typing import Union
import google
import httpx
from google import genai
from google.genai.types import GenerateContentConfigDict, GenerateContentResponse
from google.genai.errors import ClientError


class GeminiHelper:
    def __init__(
            self,
            logger: Logger,
            client: google.genai.Client,
            read_retries: int = 5,
            congestion_retries: int = 60,
            congestion_sleep_seconds: int = 10
    ):
        self.__logger = logger
        self.__client = client
        self.__congestion_sleep_seconds = congestion_sleep_seconds
        self.__congestion_retries = congestion_retries
        self.__read_retries = read_retries


    async def generate_with_retry_and_congestion_backoff(
            self,
            model_name: str,
            contents: Union[google.genai.types.ContentListUnion, google.genai.types.ContentListUnionDict],
            config: GenerateContentConfigDict) -> GenerateContentResponse:
        retries = self.__read_retries

        response: GenerateContentResponse | None = None
        last_exception: Exception | None = None
        for i in range(1, retries+1):
            try:
                response = await self.generate_with_congestion_backoff(model_name, contents, config)
                break
            except (httpx.ReadTimeout, httpx.ReadError) as e:
                last_exception = e
                self.__logger.info(f"Read error. Retrying ({i} out of {retries})")

        if response is None and last_exception is not None:
            self.__logger.info("Max retry count reached.")
            raise last_exception

        return response


    async def generate_with_congestion_backoff(
            self,
            model_name: str,
            contents: Union[google.genai.types.ContentListUnion, google.genai.types.ContentListUnionDict],
            config: GenerateContentConfigDict) -> GenerateContentResponse:
        sleep_seconds = self.__congestion_sleep_seconds
        retries = self.__congestion_retries

        response: GenerateContentResponse | None = None
        last_exception: Exception | None = None
        for i in range(1, retries+1):
            try:
                response = await self.generate(model_name, contents, config)
                break
            except ClientError as e:
                if e.code != 429:
                    raise
                last_exception = e
                self.__logger.info(f"Resource exhaustion error. Retrying in {sleep_seconds} ({i} out of {retries})")
                await asyncio.sleep(sleep_seconds)

        if response is None and last_exception is not None:
            self.__logger.info("Max retry count reached.")
            raise last_exception

        return response


    async def generate(
            self,
            model_name: str,
            contents: Union[google.genai.types.ContentListUnion, google.genai.types.ContentListUnionDict],
            config: GenerateContentConfigDict) -> GenerateContentResponse:
        return await self.__client.aio.models.generate_content(
            model=model_name,
            contents=contents,
            config=config
        )