from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "status", "attempts", "max_attempts", "created_at")
    list_filter = ("status", "type")
    search_fields = ("id", "type", "correlation_key", "locked_by")
    readonly_fields = (
        "id", "created_at", "updated_at", "locked_at", "locked_by",
        "completed_at", "attempts", "error_log",
    )
