import http
import urllib.parse
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated, List, Dict, Set, Any, Tuple
import httpx
from uuid import UUID
from sse_starlette import EventSourceResponse
from pydantic import ValidationError
from starlette.datastructures import URL
from .models import (
    AvailableModelResponse, UserResponse, JobResponse, ArtifactResponse,
    TranscriptionChunkResult, ChunkSummaryResult, GraphResult, JobStatusUpdated,
    EntityRelationResult, UpdateUserRoleRequest
)
from .config import AppConfiguration
from .services.graph_service import GraphService
from . import utils
from faststream.rabbit.fastapi import RabbitRouter, Logger
import asyncio


config = AppConfiguration()
API_URL = config.API_URL

router = RabbitRouter(config.AMQP_URL, fail_fast=False)
broker = router.broker

job_status_subscriptions: dict[UUID, list[asyncio.Queue]] = {}

app = FastAPI()
app.include_router(router)

templates = Jinja2Templates(directory="src/templates")
templates.env.globals['utils'] = utils


@router.after_startup
async def startup_broker(app: FastAPI):
    await broker.start()


@router.on_broker_shutdown
async def shutdown_broker():
    await broker.close()


async def make_api_request(path: str, method: str = "GET", json_data: dict | None = None):
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = urllib.parse.urljoin(API_URL, path)
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=json_data)
            elif method == "PUT":
                response = await client.put(url, json=json_data)
            else:
                raise ValueError(f"Неподдерживаемый метод: {method}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Ошибка сети при запросе к {url}: {e}")
            raise HTTPException(status_code=503, detail=f"Не удалось подключиться к API: {url}")
        except httpx.HTTPStatusError as e:
            print(f"Ошибка API ({e.response.status_code}) для {url}: {e.response.text}")
            detail = f"Ошибка API ({e.response.status_code})."
            try:
                api_error = e.response.json()
                if 'detail' in api_error:
                    detail = api_error['detail']
            except Exception:
                pass
            raise HTTPException(status_code=e.response.status_code, detail=detail)
        except Exception as e:
            print(f"Неожиданная ошибка при запросе к API {url}: {e}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при обращении к API.")


async def fetch_available_models() -> List[AvailableModelResponse]:
    try:
        data = await make_api_request("/models/available")
        if data:
            return [AvailableModelResponse(**item) for item in data]
        return []
    except HTTPException:
         print("Не удалось получить доступные модели от API.")
         return []


async def fetch_user_by_name(username: str) -> UserResponse | None:
    try:
        data = await make_api_request(f"/user/by-name/{username}")
        if data:
            return UserResponse(**data)
        return None
    except HTTPException as e:
        if e.status_code == 404:
            return None
        raise e


async def fetch_user_by_id(user_id: int) -> UserResponse | None:
    try:
        data = await make_api_request(f"/user/{user_id}")
        if data:
            return UserResponse(**data)
        return None
    except HTTPException as e:
        if e.status_code == 404:
            return None
        raise e


async def fetch_job(job_id: UUID) -> JobResponse:
    data = await make_api_request(f"/jobs/{job_id}")
    if data:
         try:
            return JobResponse(**data)
         except ValidationError as e:
             print(f"Ошибка валидации данных задания {job_id}: {e}")
             raise HTTPException(status_code=500, detail="Неверный формат данных задания от API.")
    raise HTTPException(status_code=500, detail="Не удалось получить данные задания от API.")


async def fetch_job_artifacts(job_id: UUID) -> List[ArtifactResponse]:
    try:
        data = await make_api_request(f"/job/{job_id}/artifacts")
        if data:
            return [ArtifactResponse(**item) for item in data]
        return []
    except HTTPException as e:
         print(f"Не удалось получить артефакты для задания {job_id}: {e.detail}")
         return []


async def create_user_api(username: str) -> UserResponse:
    data = await make_api_request("/user/register", method="POST", json_data={"username": username})
    if data:
        try:
            return UserResponse(**data)
        except ValidationError as e:
            print(f"Ошибка валидации данных пользователя при регистрации {username}: {e}")
            raise HTTPException(status_code=500, detail="Неверный формат данных пользователя от API.")
    raise HTTPException(status_code=500, detail="Не удалось создать пользователя через API.")


async def create_job_api(job_type: str, video_id: str, action_models: List[str], user_id: int) -> JobResponse:
    data = await make_api_request(
        "/jobs",
        method="POST",
        json_data={
            "type": job_type,
            "video_id": video_id,
            "action_models": action_models,
            "user_id": user_id
        }
    )
    if data:
        try:
            return JobResponse(**data)
        except ValidationError as e:
            print(f"Ошибка валидации данных задания при создании: {e}")
            raise HTTPException(status_code=500, detail="Неверный формат данных задания от API.")
    raise HTTPException(status_code=500, detail="Не удалось создать задание через API.")


async def job_status_event_generator(request: Request, job_id: UUID):
    queue: asyncio.Queue = asyncio.Queue()
    if job_id not in job_status_subscriptions:
        job_status_subscriptions[job_id] = []
    job_status_subscriptions[job_id].append(queue)
    print(f"SSE connection opened for job {job_id}")

    try:
        while True:
            if await request.is_disconnected():
                 print(f"SSE client disconnected for job {job_id}")
                 break

            try:
                status_update = await asyncio.wait_for(queue.get(), timeout=30)
                print(f"Sending status '{status_update}' for job {job_id}")
                yield {
                    "event": "status_update",
                    "data": status_update
                }
                if status_update == 'completed' or status_update == 'failed':
                    print(f"Job {job_id} finished, closing SSE stream.")
                    break
            except asyncio.TimeoutError:
                 yield {"event": "ping", "data": ""}

    except asyncio.CancelledError:
         print(f"SSE task cancelled for job {job_id}")
    finally:
        if job_id in job_status_subscriptions:
            if queue in job_status_subscriptions[job_id]:
                job_status_subscriptions[job_id].remove(queue)
            if not job_status_subscriptions[job_id]:
                del job_status_subscriptions[job_id]
                print(f"Removed last SSE subscription for job {job_id}")


async def verify_admin_role(
    request: Request,
    logger: Logger,
    admin_user_id: int | None
) -> int:
    error = None

    if admin_user_id is None:
        error = "Требуется вход администратора."
    else:
        try:
            user = await fetch_user_by_id(admin_user_id)
            if not user:
                error = "Пользователь не найден."
            elif user.role != "admin":
                error = "У пользователя нет прав администратора."
        except HTTPException as e:
            error = f"Ошибка проверки администратора: {e.detail}"
        except Exception as e:
            error = "Ошибка сервера при проверке администратора."
            logger.error(f"Unexpected error verifying admin {admin_user_id}", exc_info=True)

    if error:
        login_url = request.url_for("admin_login_get")
        final_url = login_url.replace_query_params(error=error)
        raise HTTPException(
            status_code=303,
            detail=error,
            headers={"Location": str(final_url)}
        )

    return admin_user_id


@app.get("/job_status_events/{job_id}")
async def job_status_events(request: Request, job_id: UUID):
    return EventSourceResponse(job_status_event_generator(request, job_id))


def get_graph_service():
    return GraphService()

@app.get("/graph/{job_id}/{chunk_end_ms}", response_class=HTMLResponse)
async def get_graph_chunk(
    job_id: UUID,
    chunk_end_ms: int,
    logger: Logger,
    graph_service: GraphService = Depends(get_graph_service)
):
    logger.info(f"Received request for graph chunk: job={job_id}, time={chunk_end_ms}")
    artifacts = await fetch_job_artifacts(job_id)
    graph_data: GraphResult | None = None
    entity_relation_data: EntityRelationResult | None = None

    for artifact in artifacts:
        try:
            # ensure content is dict before parsing
            if artifact.type == "graph":
                 if isinstance(artifact.content, dict):
                    try:
                        graph_data = GraphResult(**artifact.content)
                        logger.info(f"Successfully parsed graph artifact {artifact.id}")
                    except ValidationError as e:
                        logger.error(f"Validation Error parsing graph artifact {artifact.id}: {e}")
                 else:
                     logger.warning(f"Graph artifact {artifact.id} content is not a dict: {type(artifact.content)}")

            elif artifact.type == "entity-relation":
                 if isinstance(artifact.content, dict):
                    if 'entities' in artifact.content and 'relationships' in artifact.content:
                        try:
                            entity_relation_data = EntityRelationResult(**artifact.content)
                            logger.info(f"Successfully parsed entity-relation artifact {artifact.id}")
                        except ValidationError as e:
                            logger.error(f"Validation Error parsing entity-relation artifact {artifact.id}: {e}")
                    else:
                         logger.warning(f"Entity-relation artifact {artifact.id} content missing 'entities' or 'relationships' keys.")
                 else:
                      logger.warning(f"Entity-relation artifact {artifact.id} content is not a dict: {type(artifact.content)}")

        except Exception as e:
            logger.error(f"Unexpected error processing artifact {artifact.id} (type: {artifact.type}): {e}", exc_info=True)


    if not graph_data:
        logger.error(f"Graph data not found or failed to parse for job {job_id}.")
        return HTMLResponse("<p>Данные графа не найдены или повреждены.</p>", status_code=404)
    if not entity_relation_data:
         logger.error(f"Entity-relation data not found or failed to parse for job {job_id}.")
         return HTMLResponse("<p>Данные сущностей/связей не найдены или повреждены.</p>", status_code=404)

    try:
        logger.info("Calling graph_service.create_cumulative_graph_html...")
        graph_html = graph_service.create_cumulative_graph_html(
            graph_data, entity_relation_data, chunk_end_ms
        )
        logger.info(f"Graph HTML generation successful for job {job_id}, time {chunk_end_ms}.")
        return HTMLResponse(content=graph_html)
    except Exception as e:
        logger.error(f"Ошибка генерации HTML графа для задания {job_id}, интервал {chunk_end_ms}: {e}", exc_info=True)
        return HTMLResponse("<p>Ошибка при генерации графа.</p>", status_code=500)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user_id: int | None = None, message: str | None = None, error: str | None = None):
    available_models = await fetch_available_models()
    model_map = {"transcription": [], "summary": [], "graph": [], "entity-relation": []}
    for model in available_models:
        parts = model.name.split('.', 1)
        if len(parts) == 2:
            model_type, model_name = parts
            if model_type in model_map:
                model_map[model_type].append({"value": model.name, "name": model_name})

    user_id = user_id or request.query_params.get('user_id')
    message = message or request.query_params.get('message')
    error = error or request.query_params.get('error')
    if user_id:
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = None

    context = {
        "request": request,
        "model_map": model_map,
        "user_id": user_id,
        "message": message,
        "error": error
    }
    return templates.TemplateResponse("index.html", context)


@app.post("/register", response_class=RedirectResponse)
async def register_user(request: Request, username: Annotated[str, Form()]):
    message = None
    error = None
    user_id = None
    target_url: URL = request.url_for("index")
    query_params_dict = {}

    try:
        existing_user = await fetch_user_by_name(username)
        if existing_user:
            error = f"Имя пользователя '{username}' уже занято."
        else:
            new_user = await create_user_api(username)
            message = f"Пользователь '{username}' успешно зарегистрирован."
            user_id = new_user.id
    except HTTPException as e:
        error = f"Ошибка регистрации: {e.detail}"
    except Exception as e:
        error = f"Неожиданная ошибка при регистрации: {e}"
        print(f"Unexpected registration error: {e}")

    if message: query_params_dict["message"] = message
    if error: query_params_dict["error"] = error
    if user_id: query_params_dict["user_id"] = str(user_id)

    final_url = target_url.replace_query_params(**query_params_dict)

    return RedirectResponse(url=str(final_url), status_code=303)


@app.post("/login", response_class=RedirectResponse)
async def login_user(request: Request, username: Annotated[str, Form()]):
    message = None
    error = None
    user_id = None
    target_url: URL = request.url_for("index")
    query_params_dict = {}

    try:
        user = await fetch_user_by_name(username)
        if user:
            message = f"Вы вошли как '{username}'."
            user_id = user.id
        else:
            error = f"Пользователь '{username}' не найден. Пожалуйста, зарегистрируйтесь."
    except HTTPException as e:
        error = f"Ошибка входа: {e.detail}"
    except Exception as e:
        error = f"Неожиданная ошибка при входе: {e}"
        print(f"Unexpected login error: {e}")

    if message: query_params_dict["message"] = message
    if error: query_params_dict["error"] = error
    if user_id: query_params_dict["user_id"] = str(user_id)

    final_url = target_url.replace_query_params(**query_params_dict)

    return RedirectResponse(url=str(final_url), status_code=303)


@app.post("/create_job", response_class=HTMLResponse)
async def create_job(
    request: Request,
    logger: Logger,
    user_id: Annotated[int, Form()],
    job_type: Annotated[str, Form()],
    video_id: Annotated[str, Form()],
    transcription_model: Annotated[str | None, Form()] = None,
    summary_model: Annotated[str | None, Form()] = None,
    entity_relation_model: Annotated[str | None, Form()] = None,
    graph_model: Annotated[str | None, Form()] = None,
):
    action_models = []
    error = None

    if job_type == "transcription":
        if transcription_model: action_models.append(transcription_model)
        else: error = "Необходимо выбрать модель транскрипции."
    elif job_type == "summary":
        if transcription_model: action_models.append(transcription_model)
        else: error = "Необходимо выбрать модель транскрипции."
        if summary_model: action_models.append(summary_model)
        else: error = "Необходимо выбрать модель суммаризации."
    elif job_type == "graph":
        if transcription_model: action_models.append(transcription_model)
        else: error = "Необходимо выбрать модель транскрипции."
        if entity_relation_model: action_models.append(entity_relation_model)
        else: error = "Необходимо выбрать модель извлечения сущностей (entity-relation)."
        if graph_model: action_models.append(graph_model)
        else: error = "Необходимо выбрать модель построения графа."
    else:
        error = "Неизвестный тип задания."

    if error:
        available_models = await fetch_available_models()
        model_map = {"transcription": [], "summary": [], "graph": [], "entity-relation": []}
        for model in available_models:
            parts = model.name.split('.', 1)
            if len(parts) == 2:
                m_type, m_name = parts
                if m_type in model_map:
                    model_map[m_type].append({"value": model.name, "name": m_name})
        return templates.TemplateResponse("index.html", {
            "request": request, "error": error, "user_id": user_id, "model_map": model_map
        })

    try:
        job = await create_job_api(job_type, video_id, action_models, user_id)
        return RedirectResponse(url=request.url_for("job_status_page", job_id=job.id), status_code=303)
    except HTTPException as e:
        error = f"Не удалось создать задание: {e.detail}"
        available_models = await fetch_available_models()
        model_map = {"transcription": [], "summary": [], "graph": [], "entity-relation": []}
        for model in available_models:
             parts = model.name.split('.', 1)
             if len(parts) == 2:
                 m_type, m_name = parts
                 if m_type in model_map:
                     model_map[m_type].append({"value": model.name, "name": m_name})
        return templates.TemplateResponse("index.html", {
            "request": request, "error": error, "user_id": user_id, "model_map": model_map
        })


@app.get("/job/{job_id}", response_class=HTMLResponse)
async def job_status_page(
        request: Request,
        job_id: UUID,
        logger: Logger):
    try:
        job = await fetch_job(job_id)
    except HTTPException as e:
        target_url: URL = request.url_for("index")
        final_url = target_url.replace_query_params(error=f"Ошибка загрузки задания {job_id}: {e.detail}")
        return RedirectResponse(url=str(final_url), status_code=303)

    artifacts = await fetch_job_artifacts(job_id)

    processed_artifacts: Dict[str, Any] = {
        "transcription": [],
        "summary": [],
        "entity_relation": None,
        "graph": None
    }
    chunk_times: Set[Tuple[int, int]] = set()

    logger.info(f"Processing {len(artifacts)} artifacts for job {job_id}")
    for artifact in artifacts:
        try:
            content = artifact.content
            if artifact.type == "transcription" and isinstance(content, list):
                try:
                    parsed_chunks = [TranscriptionChunkResult(**chunk) for chunk in content]
                    processed_artifacts["transcription"] = parsed_chunks
                    for chunk in parsed_chunks:
                        chunk_times.add((chunk.start_time_ms, chunk.end_time_ms))
                    logger.debug(f"Processed transcription artifact {artifact.id}")
                except ValidationError as e:
                     logger.warning(f"Validation error in transcription artifact {artifact.id}: {e}")

            elif artifact.type == "summary" and isinstance(content, list):
                 try:
                    parsed_chunks = [ChunkSummaryResult(**chunk) for chunk in content]
                    processed_artifacts["summary"] = parsed_chunks
                    if not processed_artifacts["transcription"]: # Collect times if transcription missing
                        for chunk in parsed_chunks:
                            chunk_times.add((chunk.start_time_ms, chunk.end_time_ms))
                    logger.debug(f"Processed summary artifact {artifact.id}")
                 except ValidationError as e:
                     logger.warning(f"Validation error in summary artifact {artifact.id}: {e}")

            elif artifact.type == "entity-relation" and isinstance(content, dict):
                if 'entities' in content and 'relationships' in content:
                    try:
                        parsed_er = EntityRelationResult(**content)
                        processed_artifacts["entity_relation"] = parsed_er
                        if not processed_artifacts["transcription"] and not processed_artifacts["summary"]:
                             for entity in parsed_er.entities:
                                 chunk_times.add((entity.chunk_start_time_ms, entity.chunk_end_time_ms))
                             for rel in parsed_er.relationships:
                                 chunk_times.add((rel.chunk_start_time_ms, rel.chunk_end_time_ms))
                        logger.debug(f"Processed entity-relation artifact {artifact.id}")
                    except ValidationError as e:
                         logger.warning(f"Validation Error parsing entity-relation artifact {artifact.id} content: {e}")
                else:
                     logger.warning(f"Entity-relation artifact {artifact.id} content missing expected keys.")

            elif artifact.type == "graph" and isinstance(content, dict):
                 try:
                    processed_artifacts["graph"] = GraphResult(**content)
                    logger.debug(f"Processed graph artifact {artifact.id}")
                 except ValidationError as e:
                     logger.warning(f"Validation Error parsing graph artifact {artifact.id} content: {e}")

        except Exception as e:
            logger.error(f"General error processing artifact {artifact.id} (type: {artifact.type}): {e}", exc_info=True)

    sorted_chunk_end_times = sorted([t[1] for t in chunk_times])
    logger.info(f"Found {len(processed_artifacts['transcription'])} transcription chunks, {len(processed_artifacts['summary'])} summary chunks.")
    logger.info(f"EntityRelation found: {processed_artifacts['entity_relation'] is not None}, Graph found: {processed_artifacts['graph'] is not None}")
    logger.info(f"Sorted chunk end times for dropdown: {sorted_chunk_end_times}")


    context = {
        "request": request,
        "job": job,
        "artifacts": processed_artifacts,
        "sorted_chunk_end_times": sorted_chunk_end_times,
    }
    return templates.TemplateResponse("job_status.html", context)


@app.get("/admin/login", response_class=HTMLResponse, name="admin_login_get")
async def admin_login_get(
        request: Request,
        error: str | None = None):
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": error})

@app.post("/admin/login", name="admin_login_post")
async def admin_login_post(
        request: Request,
        username: Annotated[str, Form()],
        logger: Logger
):
    error = None
    admin_user_id_for_redirect = None
    try:
        user = await fetch_user_by_name(username)
        if user and user.role == "admin":
            admin_user_id_for_redirect = user.id
        else:
            error = "Неверное имя пользователя или пользователь не администратор."
    except HTTPException as e:
        error = f"Ошибка API при проверке пользователя: {e.detail}"
    except Exception as e:
         logger.error(f"Unexpected admin login error for {username}", exc_info=True)
         error = "Внутренняя ошибка сервера при входе."

    if admin_user_id_for_redirect:
        redirect_url = request.url_for('admin_dashboard')
        final_url = redirect_url.replace_query_params(admin_user_id=str(admin_user_id_for_redirect))
        return RedirectResponse(url=str(final_url), status_code=303)
    else:
        redirect_url = request.url_for('admin_login_get')
        final_url = redirect_url.replace_query_params(error=error)
        return RedirectResponse(url=str(final_url), status_code=303)


@app.get("/admin/dashboard", response_class=HTMLResponse, name="admin_dashboard")
async def admin_dashboard(
    request: Request,
    logger: Logger,
    verified_admin_id: int = Depends(verify_admin_role),
    message: str | None = None,
    error: str | None = None,
):
    users_list = []
    api_error = None
    try:
        users_data = await make_api_request("/users")
        users_list = [UserResponse(**u) for u in users_data] if users_data else []
    except HTTPException as e:
        api_error = f"Не удалось загрузить пользователей: {e.detail}"
        logger.error(api_error)
    except Exception as e:
         api_error = "Неожиданная ошибка при загрузке пользователей."
         logger.error(api_error, exc_info=True)

    display_error = error or api_error

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "users": users_list,
        "admin_user_id": verified_admin_id,
        "message": message,
        "error": display_error
    })

@app.get("/admin/monitoring", response_class=HTMLResponse, name="admin_monitoring")
async def admin_monitoring(
    request: Request,
    verified_admin_id: int = Depends(verify_admin_role)
):
    grafana_url = config.GRAFANA_DASHBOARD_URL
    return templates.TemplateResponse("admin/monitoring.html", {
        "request": request,
        "grafana_url": grafana_url,
        "admin_user_id": verified_admin_id
    })

@app.post("/admin/user/{user_id}/set-role", name="admin_set_user_role")
async def admin_set_user_role(
    request: Request,
    logger: Logger,
    user_id: int,
    role: Annotated[str, Form()],
    verified_admin_id: int = Depends(verify_admin_role),
):
    message = None
    error = None

    redirect_url = request.url_for("admin_dashboard")
    query_params_for_redirect = {"admin_user_id": str(verified_admin_id)}

    if role not in ["admin", "user"]:
         error = "Недопустимая роль."
    elif user_id == verified_admin_id:
         error = "Нельзя изменить свою роль."
    else:
        try:
            update_payload = UpdateUserRoleRequest(role=role)
            updated_user_data = await make_api_request(
                path=f"/user/{user_id}/role",
                method="PUT",
                json_data=update_payload.model_dump()
            )
            updated_user = UserResponse(**updated_user_data)
            message = f"Роль пользователя {updated_user.username} обновлена на {updated_user.role}."
        except HTTPException as e:
             error = f"Ошибка API при обновлении роли: {e.detail}"
        except ValidationError as e:
            error = f"Ошибка данных от API: {e}"
        except Exception as e:
            logger.error(f"Unexpected role update error for user {user_id}", exc_info=True)
            error = "Внутренняя ошибка сервера при обновлении роли."

    if message: query_params_for_redirect["message"] = message
    if error: query_params_for_redirect["error"] = error
    final_url = redirect_url.replace_query_params(**query_params_for_redirect)

    return RedirectResponse(url=str(final_url), status_code=303)


@router.subscriber("job.status_updated")
async def handle_job_status_updated(
        body: JobStatusUpdated,
        logger: Logger
):
    job_id = body.id
    status = body.status
    logger.info(f"Получено обновление статуса для задания {job_id}: {status}")
    if job_id in job_status_subscriptions:
        for queue in job_status_subscriptions[job_id]:
             asyncio.create_task(queue.put(status))
    else:
        logger.info(f"Нет активных SSE подписчиков для задания {job_id}")