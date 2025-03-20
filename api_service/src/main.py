from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException
import os
from faststream.rabbit import RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter, Logger

from sqlmodel import Session, select, create_engine

from models import *
from database_models import *


class AppConfiguration:
    AMQP_URL: str = os.getenv("AMQP_URL")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    MODEL_THRESHOLD: int = int(os.getenv("MODEL_AVAILABILITY_THRESHOLD", "30"))


engine = create_engine(AppConfiguration.DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    await broker.start()
    yield

router = RabbitRouter(AppConfiguration.AMQP_URL)
broker = RabbitBroker(AppConfiguration.AMQP_URL)
app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.get("/models/available", response_model=list[AvailableModelResponse])
async def get_models(
        session: Annotated[Session, Depends(get_session)]
):
    threshold = (datetime.now(timezone.utc)
                 - timedelta(seconds=AppConfiguration.MODEL_THRESHOLD))

    statement = select(AvailableModel).where(AvailableModel.last_seen >= threshold)
    models = session.exec(statement).all()

    return models

@app.post("/jobs", response_model=JobResponse)
async def create_job(
        request: CreateJobRequest,
        logger: Logger,
        session: Annotated[Session, Depends(get_session)]
):
    job = Job(**request.model_dump())
    session.add(job)
    session.commit()
    session.refresh(job)

    match job.type:
        case "transcription":
            transcription_models = [
                m for m in job.action_models
                if m.startswith("transcription.")
            ]

            if not transcription_models:
                raise HTTPException(
                    status_code=400,
                    detail="No valid transcription model specified"
                )

            model = transcription_models[0]

            await broker.publish(TranscriptionRequest(
                job_id = job.id,
                video_id = job.video_id
            ), queue=f"{model}")

            logger.info(f"Published {model}, job_id: {job.id}")

        case _:
            logger.error(f"Matching job type for {job.type} not found.")
            raise HTTPException(status_code=400, detail="Incorrect job type")

    return job

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
        job_id: UUID,
        session: Annotated[Session, Depends(get_session)]):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/user/register", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    session: Annotated[Session, Depends(get_session)]
):
    user = User(username=request.username)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.get("/user/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: Annotated[Session, Depends(get_session)]
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/user/{user_id}/jobs", response_model=list[JobResponse])
async def get_user_jobs(
        user_id: int,
        session: Annotated[Session, Depends(get_session)]
):
    statement = select(Job).where(Job.user_id == user_id)
    jobs = session.exec(statement).all()
    return jobs


@app.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: UUID,
    session: Annotated[Session, Depends(get_session)]
):
    artifact = session.get(JobArtifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@app.get("/job/{job_id}/artifacts", response_model=list[ArtifactResponse])
async def get_job_artifacts(
    job_id: UUID,
    session: Annotated[Session, Depends(get_session)]
):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    statement = select(JobArtifact).where(JobArtifact.job_id == job_id)
    models = session.exec(statement).all()

    return models


@router.subscriber("model.available")
async def handle_model_available(
        body: ModelAvailable,
        logger: Logger,
        session: Annotated[Session, Depends(get_session)]
):
    model = session.get(AvailableModel, body.model_name)

    if model:
        model.last_seen = datetime.now(timezone.utc)
    else:
        model = AvailableModel(
            name=body.model_name,
            last_seen=datetime.now(timezone.utc)
        )

    session.add(model)
    session.commit()
    logger.info(f"Updated model availability for model {body.model_name}")

@router.subscriber("transcription.result")
async def handle_transcription_result(
        body: TranscriptionResult,
        logger: Logger,
        session: Annotated[Session, Depends(get_session)]
):
    job_id = body.job_id

    logger.info(f"Handling transcription result for {job_id}...")

    job = session.get(Job, job_id)

    if not job:
        logger.error(f"Job {job_id} not found in database")
        return

    artifact = JobArtifact(
        job_id = job_id,
        type = "transcription",
        content = [chunk.model_dump() for chunk in body.result]
    )
    session.add(artifact)

    job.status = "transcription_finished"
    session.add(job)

    session.commit()
    session.refresh(artifact)

    logger.info(f"Added artifact {artifact.id}")
    logger.info(f"Updated job {job_id} status to {job.status}")
