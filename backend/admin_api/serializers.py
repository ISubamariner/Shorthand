from django.contrib.auth.models import User
from rest_framework import serializers

from admin_api.models import AuditLog, SystemSetting
from checker.models import Symbol, Word, WordTopic
from jobs.models import Job


class AdminUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_active", "is_staff", "date_joined", "last_login")
        read_only_fields = fields


class AdminUserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_active", "is_staff", "date_joined", "last_login")
        read_only_fields = ("id", "username", "email", "date_joined", "last_login")


class AdminSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = ("id", "letter", "name", "reference_image_url", "symbol_type")


class AdminWordTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordTopic
        fields = ("id", "name", "slug")
        read_only_fields = ("id",)


class AdminWordSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = Word
        fields = ("id", "text", "teeline_letters", "difficulty", "topic", "topic_name", "is_curated", "created_at")
        read_only_fields = ("id", "created_at")


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = (
            "id", "type", "status", "priority", "attempts", "max_attempts",
            "error_log", "scheduled_at", "completed_at", "created_at", "updated_at",
        )
        read_only_fields = fields


class JobDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = (
            "id", "type", "user", "correlation_key", "payload", "status",
            "priority", "attempts", "max_attempts", "error_log",
            "locked_at", "locked_by", "scheduled_at", "completed_at",
            "created_at", "updated_at",
        )
        read_only_fields = fields


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = ("id", "actor", "actor_username", "action", "target_type", "target_id", "details", "created_at")
        read_only_fields = fields


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ("id", "key", "value", "updated_at", "updated_by")
        read_only_fields = ("id", "updated_at", "updated_by")
