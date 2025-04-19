[![Build Status](https://drone.deeplerg.dev/api/badges/Deeplerg/nvideo/status.svg)](https://drone.deeplerg.dev/Deeplerg/nvideo)
[![CD Status](https://argocd.deeplerg.dev//api/badge?name=app-nvideo-prod)](https://argocd.deeplerg.dev/applications/argocd/app-nvideo-prod)

Uni group project.

Analyzes YouTube videos:
- Transcription
- Summarization
- Mind maps

As part of the requirements, uses *local* AI models.
- Whisper for ASR
- Qwen 2.5 w/ Ollama
- SentenceTransformers for generating embeddings (mind maps)

External model options have also been added.
- Gemini 2.0 Flash and Flash Lite

Stack:
- FastAPI
- RabbitMQ
- Postgres

Docker Compose for local development, Kubernetes for production. Drone CI, Argo CD.
