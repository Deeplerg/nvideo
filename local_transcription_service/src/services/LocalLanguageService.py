from ollama import chat


class LocalLanguageService:
    def __init__(self, model):
        self.model = model

    def summarize_text(self, text, max_chunk_size=2000):
        try:
            if len(text) > max_chunk_size:
                print("⚡ Текст слишком длинный, разбиваем на части...")
                chunks = [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]
                summaries = [self._summarize_chunk(chunk) for chunk in chunks]
                return "\n".join(summaries)
            return self._summarize_chunk(text)
        except Exception as e:
            print(f"❌ Ошибка при генерации резюме: {e}")
            return ""

    def _summarize_chunk(self, chunk):
        prompt = f"Сделай краткое содержание текста видео. Выдели только важные моменты. Текст должен быть на русском:\n{chunk}"
        response = chat(model=self.model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]
