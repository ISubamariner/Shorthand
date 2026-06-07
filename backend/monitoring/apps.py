import os

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitoring"

    def ready(self):
        if os.environ.get("DISABLE_MONITORING_WORKER"):
            return
        if os.environ.get("RUN_MAIN") in (None, "true"):
            from .worker import start_collector

            start_collector()
