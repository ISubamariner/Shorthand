import math
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Job


class JobRepository:
    @staticmethod
    def enqueue(
        job_type: str,
        payload: dict,
        user=None,
        correlation_key: str | None = None,
        priority: int = 0,
        max_attempts: int = 3,
    ) -> Job:
        if correlation_key:
            existing = Job.objects.filter(
                correlation_key=correlation_key,
                status__in=[Job.Status.PENDING, Job.Status.RUNNING],
            ).first()
            if existing:
                return existing

        return Job.objects.create(
            type=job_type,
            payload=payload,
            user=user,
            correlation_key=correlation_key,
            priority=priority,
            max_attempts=max_attempts,
        )

    @staticmethod
    @transaction.atomic
    def poll(worker_id: str) -> Job | None:
        now = timezone.now()
        job = (
            Job.objects
            .filter(status=Job.Status.PENDING, scheduled_at__lte=now)
            .order_by("-priority", "scheduled_at")
            .select_for_update(skip_locked=True)
            .first()
        )
        if job is None:
            return None

        job.status = Job.Status.RUNNING
        job.locked_at = now
        job.locked_by = worker_id
        job.attempts += 1
        job.save(update_fields=["status", "locked_at", "locked_by", "attempts", "updated_at"])
        return job

    @staticmethod
    def complete(job: Job) -> None:
        job.status = Job.Status.COMPLETED
        job.locked_at = None
        job.locked_by = None
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "locked_at", "locked_by", "completed_at", "updated_at"])

    @staticmethod
    def fail(job: Job, error: str) -> None:
        now = timezone.now()
        job.error_log += f"[{now.isoformat()}] {error}\n"

        if job.attempts < job.max_attempts:
            delay = min(math.pow(2, job.attempts) * 5, 300)
            job.status = Job.Status.PENDING
            job.scheduled_at = now + timedelta(seconds=delay)
            job.locked_at = None
            job.locked_by = None
        else:
            job.status = Job.Status.DEAD
            job.completed_at = now
            job.locked_at = None
            job.locked_by = None

        job.save(update_fields=[
            "status", "error_log", "scheduled_at",
            "locked_at", "locked_by", "completed_at", "updated_at",
        ])

    @staticmethod
    def reclaim_stale(minutes: int = 10) -> int:
        threshold = timezone.now() - timedelta(minutes=minutes)
        return Job.objects.filter(
            status=Job.Status.RUNNING,
            locked_at__lt=threshold,
        ).update(
            status=Job.Status.PENDING,
            locked_at=None,
            locked_by=None,
        )

    @staticmethod
    def cleanup_old(days: int = 7) -> int:
        threshold = timezone.now() - timedelta(days=days)
        count, _ = Job.objects.filter(
            status__in=[Job.Status.COMPLETED, Job.Status.DEAD],
            completed_at__lt=threshold,
        ).delete()
        return count
