import functools
import logging
from logging import Logger

from shared.models import JobFailed
from faststream.rabbit.broker.broker import RabbitBroker


def fail_job_on_exception(
        broker : RabbitBroker,
        logger : Logger = logging.getLogger(),
        queue: str = "job.failed",
        swallow_exception: bool = True):
    """
    The function must have a "body" parameter and a job_id field in that parameter.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            body = kwargs.get("body") or (args[0] if args else None)
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                job_id = getattr(body, "job_id", None)
                if job_id is not None:
                    logger.error(f"Job {job_id} failed.")

                    await broker.publish(
                        JobFailed(id=job_id),
                        queue=queue
                    )
                else:
                    logger.error(f"Job failed and job_id is None.")

                if not swallow_exception:
                    raise

                logger.exception(e)
                return None
        return wrapper
    return decorator