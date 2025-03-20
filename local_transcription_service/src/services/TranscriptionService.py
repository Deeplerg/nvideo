from .TransformerTranscriptionModel import TransformerTranscriptionModel


class TranscriptionService:
    def __init__(self, model: TransformerTranscriptionModel):
        self.model = model

    def transcribe(self, file_path):
        return self.model.transcribe(file_path)
