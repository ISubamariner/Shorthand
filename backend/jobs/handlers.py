from typing import Callable

from .models import Job

JobHandler = Callable[[Job], None]

_registry: dict[str, JobHandler] = {}


def register(job_type: str):
    def decorator(fn: JobHandler) -> JobHandler:
        _registry[job_type] = fn
        return fn
    return decorator


def get_handler(job_type: str) -> JobHandler | None:
    return _registry.get(job_type)
