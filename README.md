[![Build Status](https://drone.deeplerg.dev/api/badges/Deeplerg/nvideo/status.svg)](https://drone.deeplerg.dev/Deeplerg/nvideo)
![CD Status](https://argocd.deeplerg.dev//api/badge?name=app-nvideo-prod)

Uni group project.

Analyzes YouTube videos:
- Transcription
- Summarization
- Mind maps

As part of the requirements, uses *local* AI models.
- Whisper for ASR
- Ollama w/ Qwen 2.5 as the LLM
- SentenceTransformers for generating embeddings (mind maps)

Stack:
- FastAPI
- RabbitMQ
- Postgres

Docker Compose for local development, Kubernetes for production. Drone CI, Argo CD.
