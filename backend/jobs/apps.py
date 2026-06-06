import os

from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jobs"

    def ready(self):
        from . import predict_handler  # noqa: F401

        if os.environ.get("DISABLE_JOB_WORKERS"):
            return
        if os.environ.get("RUN_MAIN") in (None, "true"):
            from .worker import start_workers

            start_workers()
