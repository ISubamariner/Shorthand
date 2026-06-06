from django.urls import path

from .views.analytics import RetentionStatsView, UsageStatsView
from .views.audit_log import AuditLogListView
from .views.content import (
    SymbolDetailView,
    SymbolListCreateView,
    WordDetailView,
    WordListCreateView,
)
from .views.dashboard import DashboardStatsView
from .views.jobs import JobCancelView, JobDetailView, JobListView, JobRetryView
from .views.settings import SystemSettingsView
from .views.users import UserDetailView, UserListView

urlpatterns = [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="admin-dashboard-stats"),
    path("users/", UserListView.as_view(), name="admin-user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="admin-user-detail"),
    path("content/symbols/", SymbolListCreateView.as_view(), name="admin-symbol-list"),
    path("content/symbols/<int:pk>/", SymbolDetailView.as_view(), name="admin-symbol-detail"),
    path("content/words/", WordListCreateView.as_view(), name="admin-word-list"),
    path("content/words/<uuid:pk>/", WordDetailView.as_view(), name="admin-word-detail"),
    path("analytics/usage/", UsageStatsView.as_view(), name="admin-analytics-usage"),
    path("analytics/retention/", RetentionStatsView.as_view(), name="admin-analytics-retention"),
    path("jobs/", JobListView.as_view(), name="admin-job-list"),
    path("jobs/<uuid:pk>/", JobDetailView.as_view(), name="admin-job-detail"),
    path("jobs/<uuid:pk>/retry/", JobRetryView.as_view(), name="admin-job-retry"),
    path("jobs/<uuid:pk>/cancel/", JobCancelView.as_view(), name="admin-job-cancel"),
    path("audit-log/", AuditLogListView.as_view(), name="admin-audit-log"),
    path("settings/", SystemSettingsView.as_view(), name="admin-settings"),
]
