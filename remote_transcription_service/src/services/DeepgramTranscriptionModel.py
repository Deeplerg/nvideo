from logging import Logger
import httpx
from deepgram import *
from shared.transcription import TranscriptionModel

class DeepgramTranscriptionModel(TranscriptionModel):
    def __init__(
            self,
            logger: Logger,
            model_name: str,
            client: DeepgramClient):
        self.__logger = logger
        self.__model_name : str = model_name
        self.__client = client

        if "/" in self.__model_name:
            self.__model_name = self.__model_name.split('/')[-1]

    def ensure_loaded(self):
        pass

    def unload(self):
        pass

    async def transcribe(self, file_path):
        with open(file_path, "rb") as file:
            file_data = file.read()

        payload: FileSource = {
            "buffer": file_data
        }

        options = PrerecordedOptions(
            model=self.__model_name,
            smart_format=True
        )
        response: PrerecordedResponse | None = None
        retries = 5
        for i in range(1, retries):
            try:
                response = await self.__client.listen.asyncrest.v("1").transcribe_file(
                    payload, options, timeout=httpx.Timeout(300, connect=60)
                )
                break
            except httpx.ReadTimeout | httpx.ReadError:
                self.__logger.info(f"Read error. Retrying ({i} out of {retries})")

        result = response.results.channels[0].alternatives[0].transcript

        return result