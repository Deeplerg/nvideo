import gc
import torch
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq, pipeline
from ..config import *


class TransformerTranscriptionModel:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.pipe = None
        self.model = None

    def ensure_loaded(self):
        if self.pipe is None or self.model is None:
            self.__load()

    def __load(self):
        cuda_available = torch.cuda.is_available()

        device = "cuda:0" if cuda_available else "cpu"
        torch_dtype = torch.float16 if cuda_available else torch.float32

        cache_dir = AppConfiguration.TRANSCRIPTION_MODEL_DIR

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            self.model_name,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
            cache_dir=cache_dir
        )

        self.model.to(device)
        processor = AutoProcessor.from_pretrained(
            self.model_name,
            cache_dir=cache_dir)

        self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                max_new_tokens=128,
                torch_dtype=torch_dtype,
                device=device,
                return_timestamps=True
            )

    def unload(self):
        del self.model
        del self.pipe
        self.model = None
        self.pipe = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


    def transcribe(self, file_path):
        self.ensure_loaded()

        result = self.pipe(file_path)

        transcription = result["text"]

        return transcription