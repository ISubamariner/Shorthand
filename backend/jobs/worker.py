import atexit
import logging
import os
import threading
import time

import django.db

from .handlers import get_handler
from .repository import JobRepository

logger = logging.getLogger(__name__)

_shutdown = threading.Event()


def _poll_loop(worker_id: str, poll_interval: float) -> None:
    logger.info("Worker %s started (poll every %.0fs)", worker_id, poll_interval)
    while not _shutdown.is_set():
        try:
            django.db.close_old_connections()
            job = JobRepository.poll(worker_id)

            if job is None:
                _shutdown.wait(poll_interval)
                continue

            handler = get_handler(job.type)
            if handler is None:
                JobRepository.fail(job, f"No handler for job type: {job.type}")
                continue

            logger.info("Worker %s processing %s (type=%s, attempt=%d)", worker_id, job.id, job.type, job.attempts)
            handler(job)
            JobRepository.complete(job)
            logger.info("Worker %s completed %s", worker_id, job.id)

        except Exception as exc:
            if job is not None:
                logger.exception("Worker %s failed %s", worker_id, job.id)
                try:
                    JobRepository.fail(job, str(exc))
                except Exception:
                    logger.exception("Worker %s could not mark %s as failed", worker_id, job.id)
            else:
                logger.exception("Worker %s poll error", worker_id)
            _shutdown.wait(poll_interval)


def _maintenance_loop(reclaim_interval: float, cleanup_interval: float) -> None:
    logger.info("Maintenance thread started")
    last_cleanup = time.monotonic()

    while not _shutdown.is_set():
        _shutdown.wait(reclaim_interval)
        if _shutdown.is_set():
            break

        try:
            django.db.close_old_connections()
            reclaimed = JobRepository.reclaim_stale()
            if reclaimed:
                logger.info("Reclaimed %d stale jobs", reclaimed)
        except Exception:
            logger.exception("Reclaim error")

        if time.monotonic() - last_cleanup > cleanup_interval:
            try:
                cleaned = JobRepository.cleanup_old()
                if cleaned:
                    logger.info("Cleaned up %d old jobs", cleaned)
                last_cleanup = time.monotonic()
            except Exception:
                logger.exception("Cleanup error")


def start_workers() -> None:
    thread_count = int(os.environ.get("JOB_WORKER_THREADS", "2"))
    poll_interval = float(os.environ.get("JOB_POLL_INTERVAL_SECONDS", "5"))
    reclaim_interval = float(os.environ.get("JOB_RECLAIM_INTERVAL_SECONDS", "120"))
    cleanup_interval = float(os.environ.get("JOB_CLEANUP_INTERVAL_SECONDS", "86400"))

    pid = os.getpid()
    for i in range(thread_count):
        worker_id = f"w-{pid}-{i}"
        t = threading.Thread(target=_poll_loop, args=(worker_id, poll_interval), daemon=True)
        t.start()

    t = threading.Thread(target=_maintenance_loop, args=(reclaim_interval, cleanup_interval), daemon=True)
    t.start()

    atexit.register(stop_workers)
    logger.info("Started %d job workers", thread_count)


def stop_workers() -> None:
    _shutdown.set()
    logger.info("Job workers shutting down")
