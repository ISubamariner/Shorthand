import uuid

from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserScopedManager(models.Manager):
    def for_user(self, user):
        return self.filter(user=user)


class Symbol(models.Model):
    letter = models.CharField(max_length=1, unique=True)
    name = models.CharField(max_length=50)
    reference_image_url = models.URLField(blank=True, default="")

    class Meta:
        ordering = ["letter"]

    def __str__(self):
        return f"{self.letter} — {self.name}"


class Attempt(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    symbol = models.ForeignKey(
        Symbol,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    image_data = models.BinaryField(blank=True, default=b"")
    predicted_label = models.CharField(max_length=1, null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    objects = UserScopedManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} → {self.symbol.letter} ({self.status})"
