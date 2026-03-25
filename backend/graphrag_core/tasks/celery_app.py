"""Celery application configuration."""

from __future__ import annotations

from typing import Any, Callable

from backend.config.settings import settings

TASK_MODULES = ("backend.graphrag_core.tasks.workflows",)


class _ImmediateTask:
    """Fallback task wrapper used when Celery is unavailable."""

    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)

    def delay(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)


class _ImmediateCeleryApp:
    """Tiny subset of the Celery API for local development and tests."""

    def task(self, name: str | None = None) -> Callable[[Callable[..., Any]], _ImmediateTask]:
        def decorator(func: Callable[..., Any]) -> _ImmediateTask:
            return _ImmediateTask(func)

        return decorator

    def autodiscover_tasks(self, packages: list[str]) -> None:
        return None


try:
    from celery import Celery
except ImportError:
    celery_app: Any = _ImmediateCeleryApp()
else:
    celery_app = Celery(
        "mason_graphrag",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    celery_app.conf.update(
        task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        enable_utc=False,
        timezone="Asia/Hong_Kong",
        imports=TASK_MODULES,
    )
    celery_app.autodiscover_tasks(["backend.graphrag_core"], related_name="tasks")


# Explicitly import task modules so the worker always registers decorated tasks
# when started via `celery -A ...celery_app worker`.
from backend.graphrag_core.tasks import workflows as _workflows  # noqa: F401,E402
