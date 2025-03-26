import json

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Annotated, Any
import httpx
from uuid import UUID
from sse_starlette import EventSourceResponse
from .models import AvailableModelResponse, UserResponse, JobResponse, ArtifactResponse, TranscriptionChunkResult, ChunkSummaryResult, GraphResult, JobStatusUpdated
from .config import AppConfiguration
from faststream.rabbit import RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter, Logger
import asyncio

config = AppConfiguration()
API_URL = config.API_URL

router = RabbitRouter(config.AMQP_URL)
broker = RabbitBroker(config.AMQP_URL)

job_status_subscriptions: dict[UUID, list] = {}

app = FastAPI()
app.include_router(router)

app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

@router.after_startup
async def startup_broker(app: FastAPI):
    await broker.start()

@router.on_broker_shutdown
async def shutdown_broker():
    await broker.close()


async def make_api_request(path: str, method: str = "GET", json_data: dict | None = None):
    async with httpx.AsyncClient() as client:
        url = f"{API_URL}{path}"
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=json_data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP error for {url}: {e}")
            return None


async def fetch_available_models() -> list[AvailableModelResponse]:
    data = await make_api_request("/models/available")
    if data:
        return [AvailableModelResponse(**item) for item in data]
    return []

async def fetch_user_by_name(username: str) -> UserResponse | None:
    data = await make_api_request(f"/user/by-name/{username}")
    if data:
        return UserResponse(**data)
    return None

async def fetch_job_status(job_id: UUID) -> JobResponse | None:
    data = await make_api_request(f"/jobs/{job_id}")
    if data:
        return JobResponse(**data)
    return None

async def fetch_job_artifacts(job_id: UUID) -> list[ArtifactResponse]:
    data = await make_api_request(f"/job/{job_id}/artifacts")
    if data:
        return [ArtifactResponse(**item) for item in data]
    return []

async def create_user_api(username: str) -> UserResponse | None:
    data = await make_api_request("/user/register", method="POST", json_data={"username": username})
    if data:
        return UserResponse(**data)
    return None

async def create_job_api(job_type: str, video_id: str, action_models: list[str], user_id: int) -> JobResponse | None:
    data = await make_api_request("/jobs", method="POST", json_data={"type": job_type, "video_id": video_id, "action_models": action_models, "user_id": user_id})
    if data:
        return JobResponse(**data)
    return None

async def job_status_event_generator(job_id: UUID):
    queue: asyncio.Queue = asyncio.Queue()
    if job_id not in job_status_subscriptions:
        job_status_subscriptions[job_id] = []
    job_status_subscriptions[job_id].append(queue)
    try:
        while True:
            status_update = await queue.get()
            yield {
                "event": "status_update",
                "data": status_update
            }
    finally:
        job_status_subscriptions[job_id].remove(queue)
        if not job_status_subscriptions[job_id]:
            del job_status_subscriptions[job_id]


@app.get("/job_status_events/{job_id}")
async def job_status_events(job_id: UUID):
    return EventSourceResponse(job_status_event_generator(job_id))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    available_models = await fetch_available_models()
    return templates.TemplateResponse("index.html", {"request": request, "available_models": available_models})

@app.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, username: Annotated[str, Form()]):
    user = await fetch_user_by_name(username)
    if user:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Username already taken.", "available_models": await fetch_available_models()})

    user_response = await create_user_api(username)
    if user_response:
        user = await fetch_user_by_name(username)
        if user:
            return templates.TemplateResponse("index.html", {"request": request, "message": f"User {username} registered. User ID: {user.id}", "user_id": user.id, "available_models": await fetch_available_models()})
        else:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Registration failed to retrieve user details.", "available_models": await fetch_available_models()})
    else:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Registration failed.", "available_models": await fetch_available_models()})


@app.post("/login", response_class=HTMLResponse)
async def login_user(request: Request, username: Annotated[str, Form()]):
    user = await fetch_user_by_name(username)
    if user:
        return templates.TemplateResponse("index.html", {"request": request, "message": f"Logged in as {username}. User ID: {user.id}", "user_id": user.id, "available_models": await fetch_available_models()})
    else:
        return templates.TemplateResponse("index.html", {"request": request, "error": "User not found. Please register.", "available_models": await fetch_available_models()})

@app.post("/create_job", response_class=HTMLResponse)
async def create_job(
    request: Request,
    user_id: Annotated[int, Form()],
    job_type: Annotated[str, Form()],
    video_id: Annotated[str, Form()],
    action_models_form: Annotated[list[str], Form()]
):
    if not action_models_form:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Please select models for the job type.", "user_id": user_id, "available_models": await fetch_available_models()})

    job = await create_job_api(job_type, video_id, action_models_form, user_id)
    if job:
        return templates.TemplateResponse("job_status.html", {"request": request, "job": job, "job_id": job.id})
    else:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Failed to create job.", "user_id": user_id, "available_models": await fetch_available_models()})


@app.get("/job_status/{job_id}", response_class=HTMLResponse)
async def job_status_page(request: Request, job_id: UUID):
    job = await fetch_job_status(job_id)
    if not job:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Job not found.", "available_models": await fetch_available_models()})

    artifacts = await fetch_job_artifacts(job_id)

    transcription_chunks: list[TranscriptionChunkResult] = []
    summary_chunks: list[ChunkSummaryResult] = []
    graph_data: GraphResult | None = None

    for artifact in artifacts:
        try:
            # artifact.content is now already a Python dict or list thanks to Pydantic
            if artifact.type == "transcription":
                if isinstance(artifact.content, list):
                     transcription_chunks = [TranscriptionChunkResult(**chunk) for chunk in artifact.content]
                else:
                     print(f"Warning: Expected list for transcription artifact {artifact.id}, got {type(artifact.content)}")
            elif artifact.type == "summary":
                 if isinstance(artifact.content, list):
                    summary_chunks = [ChunkSummaryResult(**chunk) for chunk in artifact.content]
                 else:
                     print(f"Warning: Expected list for summary artifact {artifact.id}, got {type(artifact.content)}")
            elif artifact.type == "graph":
                if isinstance(artifact.content, dict):
                    graph_data = GraphResult(**artifact.content)
                else:
                    print(f"Warning: Expected dict for graph artifact {artifact.id}, got {type(artifact.content)}")

        except Exception as e:
            # Catch potential Pydantic validation errors or other issues
            print(f"Error processing artifact {artifact.id} (type: {artifact.type}): {e}")
            continue

    return templates.TemplateResponse(
        "job_status.html",
        {
            "request": request,
            "job": job,
            "job_id": job_id,
            "transcription_chunks": transcription_chunks,
            "summary_chunks": summary_chunks,
            "graph_data": graph_data
        }
    )

@router.subscriber("job.status_updated")
async def handle_job_status_updated(
        body: JobStatusUpdated,
        logger: Logger
):
    job_id = body.id
    status = body.status
    logger.info(f"Job status updated for job_id: {job_id} to status: {status}")
    if job_id in job_status_subscriptions:
        for queue in job_status_subscriptions[job_id]:
            await queue.put(status)