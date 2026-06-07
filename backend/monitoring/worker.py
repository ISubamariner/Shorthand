import atexit
import logging
import os
import threading

import django.db

logger = logging.getLogger(__name__)

_shutdown = threading.Event()
_worker_thread = None


def _collect_loop(interval: float, retention_days: int) -> None:
    from datetime import timedelta

    from django.utils import timezone

    from .collector import collect_snapshot
    from .models import SystemSnapshot

    logger.info(
        "Monitoring collector started (interval=%ds, retention=%dd)",
        interval,
        retention_days,
    )

    while not _shutdown.is_set():
        try:
            django.db.close_old_connections()
            data = collect_snapshot()
            SystemSnapshot.objects.create(**data)

            cutoff = timezone.now() - timedelta(days=retention_days)
            deleted, _ = SystemSnapshot.objects.filter(timestamp__lt=cutoff).delete()
            if deleted:
                logger.info("Pruned %d old snapshots", deleted)

        except Exception:
            logger.exception("Monitoring collector error")

        _shutdown.wait(interval)


def start_collector() -> None:
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return

    interval = int(os.environ.get("MONITORING_INTERVAL_SECONDS", "300"))
    retention_days = int(os.environ.get("MONITORING_RETENTION_DAYS", "7"))

    _worker_thread = threading.Thread(
        target=_collect_loop,
        args=(interval, retention_days),
        daemon=True,
    )
    _worker_thread.start()
    atexit.register(stop_collector)
    logger.info("Monitoring collector thread started")


def stop_collector() -> None:
    _shutdown.set()
    logger.info("Monitoring collector shutting down")
