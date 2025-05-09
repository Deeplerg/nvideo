﻿import logging
from asyncio import sleep
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException
from faststream.rabbit.fastapi import RabbitRouter, Logger
from sqlmodel import Session, select, create_engine
from .config import AppConfiguration
from shared.models import *
from .database_models import *
from prometheus_client import Counter, make_asgi_app


USERS_REGISTERED_COUNTER = Counter(
    'nvideo_users_registered',
    'Number of registered users'
)
TASKS_COMPLETED_COUNTER = Counter(
    'nvideo_tasks_completed',
    'Number of tasks completed by type',
    ['job_type']
)


engine = create_engine(AppConfiguration.DATABASE_URL, client_encoding="utf8")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def set_initial_admin(session: Session):
    admin_username = AppConfiguration.ADMIN_USER
    if not admin_username:
        base_logger.info("Admin user not specified")
        return

    statement = select(User).where(User.username == admin_username)
    user = session.exec(statement).first()

    if not user:
        user = User(
            username = admin_username,
            role = "admin"
        )
        base_logger.info(f"Creating admin user {admin_username}")
    else:
        user.role = "admin"
        base_logger.info(f"Setting role of {user.username} to admin")

    session.add(user)
    session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        set_initial_admin(session)

    await broker.start()

    yield


base_logger = logging.getLogger()
router = RabbitRouter(AppConfiguration.AMQP_URL, fail_fast=False)
broker = router.broker
app = FastAPI(
    lifespan=lifespan,
    root_path=AppConfiguration.ROOT_PATH
)
app.include_router(router)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


async def publish_job_updated(job: Job):
    await broker.publish(JobStatusUpdated(
        id=job.id,
        video_id=job.video_id,
        user_id=job.user_id,
        status=job.status
    ), queue="job.status_updated")

@app.get("/models/available", response_model=list[AvailableModelResponse])
async def get_models(
        session: Annotated[Session, Depends(get_session)]
):
    threshold = (datetime.now(timezone.utc)
                 - timedelta(seconds=AppConfiguration.MODEL_THRESHOLD))

    statement = select(AvailableModel).where(AvailableModel.last_seen >= threshold)
    models = session.exec(statement).all()

    return models


def first_specified_model(model_type: str, action_models : list[str]) -> str | None:
    models = [
        m for m in action_models
        if m.startswith(f"{model_type}.")
    ]

    if not models:
        return None
    return models[0]

def find_model_or_raise(model_type: str, action_models: list[str]) -> str:
    model = first_specified_model(model_type, action_models)
    if model is None:
        raise HTTPException(
            status_code=400,
            detail=f"No valid {model_type} model specified"
        )
    return model

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
        case "transcription" | "summary" | "graph":
            transcription_model = find_model_or_raise("transcription", job.action_models)

            if job.type != "transcription":
                find_model_or_raise(job.type, job.action_models)

            if job.type == "graph":
                find_model_or_raise("entity-relation", job.action_models)

            await broker.publish(TranscriptionRequest(
                job_id = job.id,
                video_id = job.video_id
            ), queue=transcription_model)

            logger.info(f"Published {transcription_model}, job_id: {job.id}")

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

    USERS_REGISTERED_COUNTER.inc()

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

@app.get("/user/by-name/{name}", response_model=UserResponse)
async def get_user_by_name(
    name: str,
    session: Annotated[Session, Depends(get_session)]
):
    statement = select(User).where(User.username == name)
    user = session.exec(statement).first()
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


@app.get("/users", response_model=list[UserResponse])
async def get_users(
        session: Annotated[Session, Depends(get_session)]
):
    statement = select(User)
    users = session.exec(statement).all()
    return users


@app.get("/users/registered_between", response_model=list[UserResponse])
async def get_users(
        start_time: int,
        end_time: int,
        session: Annotated[Session, Depends(get_session)]
):
    start_datetime = datetime.fromtimestamp(start_time, timezone.utc)
    end_datetime = datetime.fromtimestamp(end_time, timezone.utc)

    statement = select(User).where(
        User.created_at >= start_datetime,
        User.created_at <= end_datetime
    )

    users = session.exec(statement).all()
    return users


@app.put("/user/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: UpdateUserRoleRequest,
    session: Annotated[Session, Depends(get_session)],
    logger: Logger
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == role_update.role:
        return user

    user.role = role_update.role
    session.add(user)
    session.commit()
    session.refresh(user)
    logger.info(f"Updated role of user {user.username} to {user.role}")
    return user


@app.delete("/user/{user_id}", status_code=204)
async def delete_user(
        user_id: int,
        session: Annotated[Session, Depends(get_session)],
        logger: Logger
):
    user_to_delete = session.get(User, user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        session.delete(user_to_delete)
        session.commit()
        logger.info(f"Deleted user {user_id} ('{user_to_delete.username}')")
        return
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500,
                            detail="Database error during user deletion.")


@app.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: UUID,
    session: Annotated[Session, Depends(get_session)]
):
    artifact = session.get(JobArtifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return ArtifactResponse(
        id=artifact.id,
        job_id=artifact.job_id,
        type=artifact.type,
        content=artifact.content
    )


@app.get("/job/{job_id}/artifacts", response_model=list[ArtifactResponse])
async def get_job_artifacts(
    job_id: UUID,
    session: Annotated[Session, Depends(get_session)]
):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    statement = select(JobArtifact).where(JobArtifact.job_id == job_id)
    models: list[JobArtifact] = session.exec(statement).all()

    return [
        ArtifactResponse(
            id=m.id,
            job_id=m.job_id,
            type=m.type,
            content=m.content
        )
        for m in models
    ]


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
        body: TranscriptionResponse,
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

    if job.type == "transcription":
        job.status = "completed"
    else:
        job.status = "transcription_finished"
    session.add(job)

    session.commit()
    session.refresh(artifact)

    logger.info(f"Added artifact {artifact.id}")
    logger.info(f"Updated job {job_id} status to {job.status}")

    await publish_job_updated(job)

    match job.type:
        case "summary":
            model = first_specified_model(
                model_type="summary",
                action_models=job.action_models)

            request=SummaryRequest(
                job_id=job.id,
                video_id=job.video_id,
                transcription=body.result
            )

            await broker.publish(request, queue=model)
            logger.info(f"Published {model}, job_id: {job.id}")

        case "graph":
            model = first_specified_model(
                model_type="entity-relation",
                action_models=job.action_models)

            request = EntityRelationRequest(
                job_id=job.id,
                video_id=job.video_id,
                transcription=body.result
            )

            await broker.publish(request, queue=model)
            logger.info(f"Published {model}, job_id: {job.id}")

        case "transcription":
            await broker.publish(JobCompleted(
                id=job.id,
                type=job.type,
                video_id=job.video_id,
                user_id=job.user_id
            ), queue=f"job.completed")

            logger.info(f"Job {job.id} completed")

        case _:
            return


@router.subscriber("summary.result")
async def handle_summary_result(
        body: SummaryResponse,
        logger: Logger,
        session: Annotated[Session, Depends(get_session)]
):
    job_id = body.job_id

    logger.info(f"Handling summary result for {job_id}...")

    job = session.get(Job, job_id)

    if not job:
        logger.error(f"Job {job_id} not found in database")
        return

    artifact = JobArtifact(
        job_id = job_id,
        type = "summary",
        content = body.result.model_dump()
    )
    session.add(artifact)

    if job.type == "summary":
        job.status = "completed"
    else:
        job.status = "summary_finished"
    session.add(job)

    session.commit()
    session.refresh(artifact)

    logger.info(f"Added artifact {artifact.id}")
    logger.info(f"Updated job {job_id} status to {job.status}")

    await publish_job_updated(job)

    if job.type == "summary":
        await broker.publish(JobCompleted(
            id=job.id,
            type=job.type,
            video_id=job.video_id,
            user_id=job.user_id
        ), queue=f"job.completed")

        logger.info(f"Job {job.id} completed")

@router.subscriber("entity-relation.result")
async def handle_entity_relation_result(
        body: EntityRelationResponse,
        logger: Logger,
        session: Annotated[Session, Depends(get_session)]
):
    job_id = body.job_id

    logger.info(f"Handling entity-relation result for {job_id}...")

    job = session.get(Job, job_id)

    if not job:
        logger.error(f"Job {job_id} not found in database")
        return

    artifact = JobArtifact(
        job_id = job_id,
        type = "entity-relation",
        content = body.result.model_dump()
    )
    session.add(artifact)

    job.status = "entity-relation_finished"
    session.add(job)

    session.commit()
    session.refresh(artifact)

    logger.info(f"Added artifact {artifact.id}")
    logger.info(f"Updated job {job_id} status to {job.status}")

    await publish_job_updated(job)

    model = first_specified_model(
        model_type="graph",
        action_models=job.action_models)

    await broker.publish(GraphRequest(
        job_id=job.id,
        video_id=job.video_id,
        entity_relations=body.result
    ), queue=model)

    logger.info(f"Published {model}, job_id: {job.id}")

@router.subscriber("graph.result")
async def handle_graph_result(
        body: GraphResponse,
        logger: Logger,
        session: Annotated[Session, Depends(get_session)]
):
    job_id = body.job_id

    logger.info(f"Handling graph result for {job_id}...")

    job = session.get(Job, job_id)

    if not job:
        logger.error(f"Job {job_id} not found in database")
        return

    artifact = JobArtifact(
        job_id = job_id,
        type = "graph",
        content = body.result.model_dump()
    )
    session.add(artifact)

    job.status = "completed"
    session.add(job)

    session.commit()
    session.refresh(artifact)

    logger.info(f"Added artifact {artifact.id}")
    logger.info(f"Updated job {job_id} status to {job.status}")

    await publish_job_updated(job)

    await broker.publish(JobCompleted(
        id=job.id,
        type=job.type,
        video_id=job.video_id,
        user_id=job.user_id
    ), queue=f"job.completed")

    logger.info(f"Job {job.id} completed")


@router.subscriber("job.completed")
async def handle_job_completed(
        body: JobCompleted):
  TASKS_COMPLETED_COUNTER.labels(job_type=body.type).inc()

@router.subscriber("job.failed")
async def handle_summary_result(
        body: JobFailed,
        logger: Logger,
        session: Annotated[Session, Depends(get_session)]
):
    job_id = body.id

    job = session.get(Job, job_id)

    if not job:
        logger.error(f"Job {job_id} has failed but was not found in database")
        return

    logger.warning(f"Job {job_id} has failed at stage '{job.status}'. Video id: {job.video_id}, type: {job.type}")

    job.status = "failed"
    session.add(job)

    session.commit()
    session.refresh(job)

    logger.info(f"Updated job {job_id} status to {job.status}")

    await publish_job_updated(job)