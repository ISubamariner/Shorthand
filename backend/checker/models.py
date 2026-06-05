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
        null=True,
        blank=True,
    )
    anonymous_session = models.ForeignKey(
        "accounts.AnonymousSession",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="attempts",
    )
    symbol = models.ForeignKey(
        Symbol,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    word_session = models.ForeignKey(
        "WordAttemptSession",
        on_delete=models.CASCADE,
        related_name="attempts",
        null=True,
        blank=True,
    )
    word_position = models.IntegerField(null=True, blank=True)
    image_data = models.BinaryField(blank=True, default=b"")
    predicted_label = models.CharField(max_length=1, null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    points = models.IntegerField(default=0)

    objects = UserScopedManager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, anonymous_session__isnull=True)
                    | models.Q(user__isnull=True, anonymous_session__isnull=False)
                ),
                name="attempt_owner_xor",
            ),
        ]

    def __str__(self):
        if self.user_id:
            owner = self.user.username
        elif self.anonymous_session_id:
            owner = f"Session {str(self.anonymous_session.session_token)[:8]}"
        else:
            owner = "unknown"
        return f"{owner} → {self.symbol.letter} ({self.status})"


class UserStats(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="stats",
    )
    anonymous_session = models.OneToOneField(
        "accounts.AnonymousSession",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="stats",
    )
    total_score = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, anonymous_session__isnull=True)
                    | models.Q(user__isnull=True, anonymous_session__isnull=False)
                ),
                name="userstats_owner_xor",
            ),
        ]

    def __str__(self):
        if self.user_id:
            owner = self.user.username
        elif self.anonymous_session_id:
            owner = f"Session {str(self.anonymous_session.session_token)[:8]}"
        else:
            owner = "unknown"
        return f"Stats for {owner}"


class WordTopic(TimestampedModel):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Word(TimestampedModel):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"

    text = models.CharField(max_length=100, unique=True)
    teeline_letters = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=12, choices=Difficulty.choices)
    topic = models.ForeignKey(
        WordTopic,
        on_delete=models.CASCADE,
        related_name="words",
    )
    is_curated = models.BooleanField(default=False)

    class Meta:
        ordering = ["text"]

    def __str__(self):
        return f"{self.text} → {self.teeline_letters}"


class WordAttemptSession(TimestampedModel):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        ABANDONED = "abandoned"

    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="word_sessions",
        null=True,
        blank=True,
    )
    anonymous_session = models.ForeignKey(
        "accounts.AnonymousSession",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="word_sessions",
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    letters_correct = models.IntegerField(default=0)
    letters_total = models.IntegerField(default=0)
    points_awarded = models.IntegerField(default=0)

    objects = UserScopedManager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, anonymous_session__isnull=True)
                    | models.Q(user__isnull=True, anonymous_session__isnull=False)
                ),
                name="word_session_owner_xor",
            ),
        ]

    def __str__(self):
        owner = self.user.username if self.user else f"Session {str(self.anonymous_session.session_token)[:8]}"
        return f"{owner} → {self.word.text} ({self.status})"
