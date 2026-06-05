import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Job(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        DEAD = "dead"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=50, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobs",
    )
    correlation_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    priority = models.IntegerField(default=0)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    error_log = models.TextField(default="", blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=100, null=True, blank=True)
    scheduled_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "scheduled_at"]
        indexes = [
            models.Index(
                fields=["status", "scheduled_at"],
                name="idx_job_poll",
            ),
        ]

    def __str__(self):
        return f"{self.type} [{self.status}] ({self.id})"
