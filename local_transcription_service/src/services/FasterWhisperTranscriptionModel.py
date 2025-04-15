import gc
import torch
from faster_whisper import WhisperModel
from shared.transcription import *
from ..config import *


class FasterWhisperTranscriptionModel(TranscriptionModel):
    def __init__(self, model_name: str):
        self.model_name : str = model_name
        self.model : WhisperModel | None = None

        if "/" in self.model_name:
            self.model_name = self.model_name.split('/')[-1]

    def ensure_loaded(self):
        if self.model is None:
            self.__load()

    def __load(self):
        cuda_available = torch.cuda.is_available()

        device = "cuda" if cuda_available else "cpu"

        # https://opennmt.net/CTranslate2/quantization.html
        # "By default, the runtime tries to use the type that is saved in the converted model as the computation type."
        #compute_type = "float16" if cuda_available else "float32"

        cache_dir = AppConfiguration.TRANSCRIPTION_MODEL_DIR

        self.model = WhisperModel(
            model_size_or_path=self.model_name,
            download_root=cache_dir,
            device=device,
            #compute_type=compute_type
        )

    def unload(self):
        del self.model
        self.model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


    def transcribe(self, file_path):
        self.ensure_loaded()

        segments, info = self.model.transcribe(
            audio=file_path
        )

        result = " ".join(segment.text for segment in segments)

        return result