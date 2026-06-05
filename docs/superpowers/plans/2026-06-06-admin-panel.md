# Admin Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an admin panel at `/admin` with user management, content CRUD, analytics, job monitoring, audit logging, and system settings — gated by Django's `is_staff` flag.

**Architecture:** New `admin_api` Django app with DRF viewsets under `/api/admin/`. React frontend gets a lazy-loaded `/admin/*` route tree with a dedicated dashboard layout (sidebar + topbar). Two new models: `AuditLog` and `SystemSetting`. Existing `Job` model gets read endpoints. Auth uses existing JWT flow; authorization checks `is_staff`.

**Tech Stack:** Django 5.1 + DRF, React 18 + React Router 6 + Vite, plain CSS with CSS custom properties, PostgreSQL.

**Spec:** `docs/superpowers/specs/2026-06-06-admin-panel-design.md`

---

## File Map

### Backend — New `admin_api` app

| File | Responsibility |
|------|---------------|
| `backend/admin_api/__init__.py` | App init |
| `backend/admin_api/apps.py` | Django app config |
| `backend/admin_api/models.py` | `AuditLog` and `SystemSetting` models |
| `backend/admin_api/serializers.py` | All admin serializers |
| `backend/admin_api/permissions.py` | `IsAdminUser` permission (thin wrapper) |
| `backend/admin_api/views/dashboard.py` | Dashboard stats endpoint |
| `backend/admin_api/views/users.py` | User list/detail/edit/reset-password |
| `backend/admin_api/views/content.py` | Symbol and Word CRUD |
| `backend/admin_api/views/analytics.py` | Usage, leaderboard, retention |
| `backend/admin_api/views/jobs.py` | Job list/detail/retry/cancel |
| `backend/admin_api/views/audit_log.py` | Audit log list |
| `backend/admin_api/views/settings.py` | System settings get/patch |
| `backend/admin_api/views/__init__.py` | Package init |
| `backend/admin_api/services.py` | Audit log helper, dashboard aggregation |
| `backend/admin_api/urls.py` | URL routing for `/api/admin/` |
| `backend/admin_api/management/commands/make_admin.py` | Management command |
| `backend/admin_api/tests.py` | All admin API tests |

### Backend — Modified files

| File | Change |
|------|--------|
| `backend/config/settings/base.py` | Add `"admin_api"` to `INSTALLED_APPS` |
| `backend/config/urls.py` | Add `path("api/admin/", include("admin_api.urls"))` |
| `backend/accounts/serializers.py` | Add `is_staff` to `UserSerializer.Meta.fields` |

### Frontend — New files

| File | Responsibility |
|------|---------------|
| `frontend/src/pages/admin/AdminLayout.tsx` | Sidebar + topbar shell |
| `frontend/src/pages/admin/DashboardPage.tsx` | Overview stats |
| `frontend/src/pages/admin/UsersPage.tsx` | User list |
| `frontend/src/pages/admin/UserDetailPage.tsx` | Single user view/edit |
| `frontend/src/pages/admin/ContentPage.tsx` | Symbols & words CRUD |
| `frontend/src/pages/admin/AnalyticsPage.tsx` | Usage charts & stats |
| `frontend/src/pages/admin/JobsPage.tsx` | Job queue monitoring |
| `frontend/src/pages/admin/AuditLogPage.tsx` | Admin action history |
| `frontend/src/pages/admin/SettingsPage.tsx` | System configuration |
| `frontend/src/components/admin/AdminRoute.tsx` | Auth guard + lazy loader |
| `frontend/src/components/admin/DataTable.tsx` | Reusable sortable table |
| `frontend/src/components/admin/StatCard.tsx` | Dashboard stat card |
| `frontend/src/components/admin/Pagination.tsx` | Pagination controls |
| `frontend/src/components/admin/ActionConfirm.tsx` | Destructive action modal |
| `frontend/src/api/admin.ts` | Admin API client |
| `frontend/src/styles/admin.css` | Admin-specific styles |
| `frontend/src/types/admin.ts` | Admin type definitions |

### Frontend — Modified files

| File | Change |
|------|--------|
| `frontend/src/App.tsx` | Add lazy-loaded `/admin/*` routes |
| `frontend/src/types/index.ts` | Add `is_staff` to `User` type |

---

## Task 1: Backend Models & Migrations

**Files:**
- Create: `backend/admin_api/__init__.py`
- Create: `backend/admin_api/apps.py`
- Create: `backend/admin_api/models.py`
- Modify: `backend/config/settings/base.py`

- [ ] **Step 1: Create app directory and config**

```bash
mkdir -p backend/admin_api/management/commands backend/admin_api/views
touch backend/admin_api/__init__.py backend/admin_api/views/__init__.py backend/admin_api/management/__init__.py backend/admin_api/management/commands/__init__.py
```

- [ ] **Step 2: Write `apps.py`**

Create `backend/admin_api/apps.py`:

```python
from django.apps import AppConfig


class AdminApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_api"
```

- [ ] **Step 3: Write models**

Create `backend/admin_api/models.py`:

```python
import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=50, db_index=True)
    target_id = models.CharField(max_length=255)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor} → {self.action} ({self.target_type}:{self.target_id})"


class SystemSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key
```

- [ ] **Step 4: Register app in settings**

In `backend/config/settings/base.py`, add `"admin_api"` to `INSTALLED_APPS` after `"jobs"`:

```python
INSTALLED_APPS = [
    ...
    "accounts",
    "checker",
    "jobs",
    "admin_api",
]
```

- [ ] **Step 5: Generate and run migrations**

```bash
cd backend && python manage.py makemigrations admin_api && python manage.py migrate
```

Expected: migration creates `auditlog` and `systemsetting` tables.

- [ ] **Step 6: Commit**

```bash
git add backend/admin_api/ backend/config/settings/base.py
git commit -m "feat(admin): add admin_api app with AuditLog and SystemSetting models"
```

---

## Task 2: Permissions, Audit Helper & Management Command

**Files:**
- Create: `backend/admin_api/permissions.py`
- Create: `backend/admin_api/services.py`
- Create: `backend/admin_api/management/commands/make_admin.py`
- Test: `backend/admin_api/tests.py`

- [ ] **Step 1: Write tests for permission, audit helper, and management command**

Create `backend/admin_api/tests.py`:

```python
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from admin_api.models import AuditLog
from admin_api.permissions import IsAdminUser
from admin_api.services import log_audit


class IsAdminUserPermissionTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsAdminUser()

    def test_staff_user_allowed(self):
        user = User.objects.create_user("admin", password="testpass1234", is_staff=True)
        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_regular_user_denied(self):
        user = User.objects.create_user("user", password="testpass1234")
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_anonymous_denied(self):
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))


class LogAuditTest(TestCase):
    def test_creates_audit_entry(self):
        user = User.objects.create_user("admin", password="testpass1234", is_staff=True)
        log_audit(
            actor=user,
            action="user.deactivate",
            target_type="user",
            target_id="123",
            details={"before": {"is_active": True}, "after": {"is_active": False}},
        )
        entry = AuditLog.objects.get()
        self.assertEqual(entry.actor, user)
        self.assertEqual(entry.action, "user.deactivate")
        self.assertEqual(entry.target_type, "user")
        self.assertEqual(entry.target_id, "123")
        self.assertEqual(entry.details["before"]["is_active"], True)


class MakeAdminCommandTest(TestCase):
    def test_promotes_user_to_staff(self):
        User.objects.create_user("alice", password="testpass1234")
        out = StringIO()
        call_command("make_admin", "alice", stdout=out)
        self.assertTrue(User.objects.get(username="alice").is_staff)
        self.assertIn("alice", out.getvalue())

    def test_nonexistent_user_errors(self):
        out = StringIO()
        err = StringIO()
        call_command("make_admin", "nobody", stdout=out, stderr=err)
        self.assertIn("not found", err.getvalue())
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python manage.py test admin_api -v2
```

Expected: ImportError — `admin_api.permissions` and `admin_api.services` do not exist yet.

- [ ] **Step 3: Write permission class**

Create `backend/admin_api/permissions.py`:

```python
from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
```

- [ ] **Step 4: Write audit helper**

Create `backend/admin_api/services.py`:

```python
from admin_api.models import AuditLog


def log_audit(actor, action, target_type, target_id, details=None):
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        details=details or {},
    )
```

- [ ] **Step 5: Write management command**

Create `backend/admin_api/management/commands/make_admin.py`:

```python
import sys

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Grant admin (is_staff) access to a user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(f'User "{username}" not found.')
            return

        user.is_staff = True
        user.save(update_fields=["is_staff"])
        self.stdout.write(f'User "{username}" is now an admin.')
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd backend && python manage.py test admin_api -v2
```

Expected: all 5 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/admin_api/permissions.py backend/admin_api/services.py backend/admin_api/management/ backend/admin_api/tests.py
git commit -m "feat(admin): add IsAdminUser permission, audit logger, and make_admin command"
```

---

## Task 3: Serializers & UserSerializer Update

**Files:**
- Create: `backend/admin_api/serializers.py`
- Modify: `backend/accounts/serializers.py`

- [ ] **Step 1: Write tests for serializers**

Append to `backend/admin_api/tests.py`:

```python
from django.utils import timezone

from checker.models import Symbol, Word, WordTopic
from jobs.models import Job

from admin_api.serializers import (
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    AdminSymbolSerializer,
    AdminWordSerializer,
    AuditLogSerializer,
    JobSerializer,
    SystemSettingSerializer,
)


class AdminUserListSerializerTest(TestCase):
    def test_serializes_user_list_fields(self):
        user = User.objects.create_user("alice", email="a@b.com", password="testpass1234")
        data = AdminUserListSerializer(user).data
        self.assertEqual(data["username"], "alice")
        self.assertEqual(data["email"], "a@b.com")
        self.assertIn("id", data)
        self.assertIn("is_active", data)
        self.assertIn("is_staff", data)
        self.assertIn("date_joined", data)


class AdminSymbolSerializerTest(TestCase):
    def test_serializes_symbol(self):
        symbol = Symbol.objects.create(letter="a", name="Alpha")
        data = AdminSymbolSerializer(symbol).data
        self.assertEqual(data["letter"], "a")
        self.assertEqual(data["name"], "Alpha")
        self.assertIn("id", data)


class JobSerializerTest(TestCase):
    def test_serializes_job(self):
        job = Job.objects.create(type="process_attempt", status="pending")
        data = JobSerializer(job).data
        self.assertEqual(data["type"], "process_attempt")
        self.assertEqual(data["status"], "pending")
        self.assertIn("id", data)
        self.assertIn("created_at", data)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python manage.py test admin_api -v2
```

Expected: ImportError — `admin_api.serializers` does not exist yet.

- [ ] **Step 3: Write serializers**

Create `backend/admin_api/serializers.py`:

```python
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
        fields = ("id", "letter", "name", "reference_image_url")


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
```

- [ ] **Step 4: Add `is_staff` to accounts UserSerializer**

In `backend/accounts/serializers.py`, update `UserSerializer`:

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_staff")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && python manage.py test admin_api -v2
```

Expected: all 8 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/admin_api/serializers.py backend/accounts/serializers.py backend/admin_api/tests.py
git commit -m "feat(admin): add admin serializers and expose is_staff in UserSerializer"
```

---

## Task 4: Dashboard & User Management Views

**Files:**
- Create: `backend/admin_api/views/dashboard.py`
- Create: `backend/admin_api/views/users.py`

- [ ] **Step 1: Write tests for dashboard and user views**

Append to `backend/admin_api/tests.py`:

```python
from rest_framework.test import APIClient


class AdminViewTestBase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            "admin", email="admin@test.com", password="testpass1234", is_staff=True
        )
        self.user = User.objects.create_user(
            "regular", email="user@test.com", password="testpass1234"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)


class DashboardStatsViewTest(AdminViewTestBase):
    def test_returns_stats(self):
        response = self.client.get("/api/admin/dashboard/stats/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("user_count", response.data)
        self.assertIn("attempt_count", response.data)

    def test_non_admin_denied(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/admin/dashboard/stats/")
        self.assertEqual(response.status_code, 403)


class UserListViewTest(AdminViewTestBase):
    def test_lists_users(self):
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

    def test_search_by_username(self):
        response = self.client.get("/api/admin/users/?search=admin")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["username"], "admin")

    def test_non_admin_denied(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/admin/users/")
        self.assertEqual(response.status_code, 403)


class UserDetailViewTest(AdminViewTestBase):
    def test_get_user_detail(self):
        response = self.client.get(f"/api/admin/users/{self.user.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "regular")

    def test_patch_user(self):
        response = self.client.patch(
            f"/api/admin/users/{self.user.id}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        audit = AuditLog.objects.get()
        self.assertEqual(audit.action, "user.update")

    def test_non_admin_denied(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/admin/users/{self.admin.id}/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python manage.py test admin_api.tests.DashboardStatsViewTest admin_api.tests.UserListViewTest admin_api.tests.UserDetailViewTest -v2
```

Expected: 404 errors — URL routes don't exist yet.

- [ ] **Step 3: Write dashboard view**

Create `backend/admin_api/views/dashboard.py`:

```python
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminUser
from checker.models import Attempt
from jobs.models import Job


class DashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        return Response({
            "user_count": User.objects.count(),
            "attempt_count": Attempt.objects.count(),
            "active_today": User.objects.filter(last_login__date=today).count(),
            "pending_jobs": Job.objects.filter(status=Job.Status.PENDING).count(),
            "failed_jobs": Job.objects.filter(status=Job.Status.FAILED).count(),
        })
```

- [ ] **Step 4: Write user views**

Create `backend/admin_api/views/users.py`:

```python
from django.contrib.auth.models import User
from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView

from admin_api.permissions import IsAdminUser
from admin_api.serializers import AdminUserListSerializer, AdminUserDetailSerializer
from admin_api.services import log_audit


class UserListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserListSerializer
    queryset = User.objects.all().order_by("-date_joined")
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email"]


class UserDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserDetailSerializer
    queryset = User.objects.all()

    def perform_update(self, serializer):
        before = {f: getattr(self.get_object(), f) for f in serializer.validated_data}
        instance = serializer.save()
        after = {f: getattr(instance, f) for f in serializer.validated_data}
        log_audit(
            actor=self.request.user,
            action="user.update",
            target_type="user",
            target_id=instance.pk,
            details={"before": before, "after": after},
        )
```

- [ ] **Step 5: Run tests to verify they still fail (no URLs yet)**

We'll wire URLs in Task 7.

- [ ] **Step 6: Commit**

```bash
git add backend/admin_api/views/dashboard.py backend/admin_api/views/users.py backend/admin_api/tests.py
git commit -m "feat(admin): add dashboard stats and user management views"
```

---

## Task 5: Content, Analytics & Settings Views

**Files:**
- Create: `backend/admin_api/views/content.py`
- Create: `backend/admin_api/views/analytics.py`
- Create: `backend/admin_api/views/settings.py`

- [ ] **Step 1: Write tests for content, analytics, and settings views**

Append to `backend/admin_api/tests.py`:

```python
class SymbolContentViewTest(AdminViewTestBase):
    def test_list_symbols(self):
        Symbol.objects.create(letter="a", name="Alpha")
        response = self.client.get("/api/admin/content/symbols/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_create_symbol(self):
        response = self.client.post(
            "/api/admin/content/symbols/",
            {"letter": "b", "name": "Bravo"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Symbol.objects.filter(letter="b").exists())
        self.assertTrue(AuditLog.objects.filter(action="content.symbol.create").exists())

    def test_delete_symbol(self):
        symbol = Symbol.objects.create(letter="c", name="Charlie")
        response = self.client.delete(f"/api/admin/content/symbols/{symbol.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Symbol.objects.filter(id=symbol.id).exists())
        self.assertTrue(AuditLog.objects.filter(action="content.symbol.delete").exists())


class WordContentViewTest(AdminViewTestBase):
    def test_list_words(self):
        topic = WordTopic.objects.create(name="Greetings", slug="greetings")
        Word.objects.create(text="hello", teeline_letters="hl", difficulty="beginner", topic=topic)
        response = self.client.get("/api/admin/content/words/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class AnalyticsViewTest(AdminViewTestBase):
    def test_usage_stats(self):
        response = self.client.get("/api/admin/analytics/usage/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("daily", response.data)

    def test_non_admin_denied(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/admin/analytics/usage/")
        self.assertEqual(response.status_code, 403)


class SystemSettingsViewTest(AdminViewTestBase):
    def test_get_settings(self):
        from admin_api.models import SystemSetting
        SystemSetting.objects.create(key="maintenance_mode", value=False, updated_by=self.admin)
        response = self.client.get("/api/admin/settings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_patch_settings(self):
        from admin_api.models import SystemSetting
        setting = SystemSetting.objects.create(key="maintenance_mode", value=False, updated_by=self.admin)
        response = self.client.patch(
            "/api/admin/settings/",
            [{"key": "maintenance_mode", "value": True}],
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        setting.refresh_from_db()
        self.assertTrue(setting.value)
        self.assertTrue(AuditLog.objects.filter(action="settings.update").exists())
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python manage.py test admin_api.tests.SymbolContentViewTest admin_api.tests.WordContentViewTest admin_api.tests.AnalyticsViewTest admin_api.tests.SystemSettingsViewTest -v2
```

Expected: failures — views don't exist yet.

- [ ] **Step 3: Write content views**

Create `backend/admin_api/views/content.py`:

```python
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from admin_api.permissions import IsAdminUser
from admin_api.serializers import AdminSymbolSerializer, AdminWordSerializer
from admin_api.services import log_audit
from checker.models import Symbol, Word


class SymbolListCreateView(ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminSymbolSerializer
    queryset = Symbol.objects.all()
    pagination_class = None

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(
            actor=self.request.user,
            action="content.symbol.create",
            target_type="symbol",
            target_id=instance.pk,
            details={"data": serializer.data},
        )


class SymbolDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminSymbolSerializer
    queryset = Symbol.objects.all()

    def perform_update(self, serializer):
        before = AdminSymbolSerializer(self.get_object()).data
        instance = serializer.save()
        log_audit(
            actor=self.request.user,
            action="content.symbol.update",
            target_type="symbol",
            target_id=instance.pk,
            details={"before": before, "after": serializer.data},
        )

    def perform_destroy(self, instance):
        data = AdminSymbolSerializer(instance).data
        pk = instance.pk
        instance.delete()
        log_audit(
            actor=self.request.user,
            action="content.symbol.delete",
            target_type="symbol",
            target_id=pk,
            details={"data": data},
        )


class WordListCreateView(ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminWordSerializer
    queryset = Word.objects.select_related("topic").all()
    pagination_class = None

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(
            actor=self.request.user,
            action="content.word.create",
            target_type="word",
            target_id=instance.pk,
            details={"data": serializer.data},
        )


class WordDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminWordSerializer
    queryset = Word.objects.select_related("topic").all()

    def perform_update(self, serializer):
        before = AdminWordSerializer(self.get_object()).data
        instance = serializer.save()
        log_audit(
            actor=self.request.user,
            action="content.word.update",
            target_type="word",
            target_id=instance.pk,
            details={"before": before, "after": serializer.data},
        )

    def perform_destroy(self, instance):
        data = AdminWordSerializer(instance).data
        pk = instance.pk
        instance.delete()
        log_audit(
            actor=self.request.user,
            action="content.word.delete",
            target_type="word",
            target_id=pk,
            details={"data": data},
        )
```

- [ ] **Step 4: Write analytics view**

Create `backend/admin_api/views/analytics.py`:

```python
from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminUser
from checker.models import Attempt


class UsageStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)
        daily = (
            Attempt.objects.filter(created_at__gte=since)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return Response({
            "daily": [{"date": str(row["date"]), "count": row["count"]} for row in daily],
            "total": Attempt.objects.filter(created_at__gte=since).count(),
        })


class RetentionStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.contrib.auth.models import User

        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)
        total = User.objects.count()
        active = User.objects.filter(last_login__gte=since).count()
        return Response({
            "total_users": total,
            "active_users": active,
            "retention_rate": round(active / total * 100, 1) if total else 0,
        })
```

- [ ] **Step 5: Write settings view**

Create `backend/admin_api/views/settings.py`:

```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.models import SystemSetting
from admin_api.permissions import IsAdminUser
from admin_api.serializers import SystemSettingSerializer
from admin_api.services import log_audit


class SystemSettingsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        settings = SystemSetting.objects.all()
        return Response(SystemSettingSerializer(settings, many=True).data)

    def patch(self, request):
        updated = []
        for item in request.data:
            key = item.get("key")
            value = item.get("value")
            try:
                setting = SystemSetting.objects.get(key=key)
                before = setting.value
                setting.value = value
                setting.updated_by = request.user
                setting.save()
                log_audit(
                    actor=request.user,
                    action="settings.update",
                    target_type="setting",
                    target_id=key,
                    details={"before": before, "after": value},
                )
                updated.append(setting)
            except SystemSetting.DoesNotExist:
                continue
        return Response(SystemSettingSerializer(updated, many=True).data)
```

- [ ] **Step 6: Commit**

```bash
git add backend/admin_api/views/content.py backend/admin_api/views/analytics.py backend/admin_api/views/settings.py backend/admin_api/tests.py
git commit -m "feat(admin): add content CRUD, analytics, and settings views"
```

---

## Task 6: Jobs & Audit Log Views

**Files:**
- Create: `backend/admin_api/views/jobs.py`
- Create: `backend/admin_api/views/audit_log.py`

- [ ] **Step 1: Write tests for job and audit log views**

Append to `backend/admin_api/tests.py`:

```python
class JobViewTest(AdminViewTestBase):
    def test_list_jobs(self):
        Job.objects.create(type="process_attempt", status="pending")
        response = self.client.get("/api/admin/jobs/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_filter_jobs_by_status(self):
        Job.objects.create(type="process_attempt", status="pending")
        Job.objects.create(type="process_attempt", status="failed")
        response = self.client.get("/api/admin/jobs/?status=failed")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_retry_failed_job(self):
        job = Job.objects.create(type="process_attempt", status="failed", attempts=1)
        response = self.client.post(f"/api/admin/jobs/{job.id}/retry/")
        self.assertEqual(response.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.status, "pending")
        self.assertTrue(AuditLog.objects.filter(action="job.retry").exists())

    def test_retry_non_failed_job_rejected(self):
        job = Job.objects.create(type="process_attempt", status="completed")
        response = self.client.post(f"/api/admin/jobs/{job.id}/retry/")
        self.assertEqual(response.status_code, 400)

    def test_cancel_pending_job(self):
        job = Job.objects.create(type="process_attempt", status="pending")
        response = self.client.post(f"/api/admin/jobs/{job.id}/cancel/")
        self.assertEqual(response.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.status, "dead")
        self.assertTrue(AuditLog.objects.filter(action="job.cancel").exists())


class AuditLogViewTest(AdminViewTestBase):
    def test_list_audit_logs(self):
        log_audit(actor=self.admin, action="user.update", target_type="user", target_id="1")
        response = self.client.get("/api/admin/audit-log/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_action(self):
        log_audit(actor=self.admin, action="user.update", target_type="user", target_id="1")
        log_audit(actor=self.admin, action="content.symbol.create", target_type="symbol", target_id="2")
        response = self.client.get("/api/admin/audit-log/?action=user.update")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_non_admin_denied(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/admin/audit-log/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python manage.py test admin_api.tests.JobViewTest admin_api.tests.AuditLogViewTest -v2
```

Expected: 404 errors — views and URLs don't exist yet.

- [ ] **Step 3: Write jobs view**

Create `backend/admin_api/views/jobs.py`:

```python
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminUser
from admin_api.serializers import JobSerializer, JobDetailSerializer
from admin_api.services import log_audit
from jobs.models import Job


class JobListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = JobSerializer
    queryset = Job.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        job_status = self.request.query_params.get("status")
        if job_status:
            qs = qs.filter(status=job_status)
        return qs


class JobDetailView(RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = JobDetailSerializer
    queryset = Job.objects.all()


class JobRetryView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if job.status not in (Job.Status.FAILED, Job.Status.DEAD):
            return Response(
                {"detail": "Only failed or dead jobs can be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.status = Job.Status.PENDING
        job.error_log = ""
        job.locked_at = None
        job.locked_by = None
        job.save(update_fields=["status", "error_log", "locked_at", "locked_by", "updated_at"])
        log_audit(
            actor=request.user,
            action="job.retry",
            target_type="job",
            target_id=job.pk,
        )
        return Response(JobSerializer(job).data)


class JobCancelView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if job.status != Job.Status.PENDING:
            return Response(
                {"detail": "Only pending jobs can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.status = Job.Status.DEAD
        job.save(update_fields=["status", "updated_at"])
        log_audit(
            actor=request.user,
            action="job.cancel",
            target_type="job",
            target_id=job.pk,
        )
        return Response(JobSerializer(job).data)
```

- [ ] **Step 4: Write audit log view**

Create `backend/admin_api/views/audit_log.py`:

```python
from rest_framework.generics import ListAPIView

from admin_api.models import AuditLog
from admin_api.permissions import IsAdminUser
from admin_api.serializers import AuditLogSerializer


class AuditLogListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("actor").all()

    def get_queryset(self):
        qs = super().get_queryset()
        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)
        actor = self.request.query_params.get("actor")
        if actor:
            qs = qs.filter(actor__username=actor)
        target_type = self.request.query_params.get("target_type")
        if target_type:
            qs = qs.filter(target_type=target_type)
        return qs
```

- [ ] **Step 5: Commit**

```bash
git add backend/admin_api/views/jobs.py backend/admin_api/views/audit_log.py backend/admin_api/tests.py
git commit -m "feat(admin): add job management and audit log views"
```

---

## Task 7: URL Routing & Full Backend Test Run

**Files:**
- Create: `backend/admin_api/urls.py`
- Modify: `backend/config/urls.py`

- [ ] **Step 1: Write URL config**

Create `backend/admin_api/urls.py`:

```python
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
```

- [ ] **Step 2: Wire admin URLs into main config**

In `backend/config/urls.py`, add the admin_api include. Note: Django's built-in admin is at `admin/` — our API is at `api/admin/`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/admin/", include("admin_api.urls")),
    path("api/", include("checker.urls")),
]
```

- [ ] **Step 3: Run all admin tests**

```bash
cd backend && python manage.py test admin_api -v2
```

Expected: all tests pass (permission tests, serializer tests, view tests).

- [ ] **Step 4: Run full backend test suite to check for regressions**

```bash
cd backend && python manage.py test -v2
```

Expected: all existing tests plus new admin tests pass. The `is_staff` addition to `UserSerializer` should not break existing tests since it's a new read-only field.

- [ ] **Step 5: Commit**

```bash
git add backend/admin_api/urls.py backend/config/urls.py
git commit -m "feat(admin): wire admin API URLs and verify all tests pass"
```

---

## Task 8: Frontend Types & Admin API Client

**Files:**
- Create: `frontend/src/types/admin.ts`
- Create: `frontend/src/api/admin.ts`
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Add `is_staff` to User type**

In `frontend/src/types/index.ts`, add `is_staff` to the `User` interface:

```typescript
export interface User {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
}
```

- [ ] **Step 2: Create admin type definitions**

Create `frontend/src/types/admin.ts`:

```typescript
export interface AdminUser {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface DashboardStats {
  user_count: number;
  attempt_count: number;
  active_today: number;
  pending_jobs: number;
  failed_jobs: number;
}

export interface AdminSymbol {
  id: number;
  letter: string;
  name: string;
  reference_image_url: string;
}

export interface AdminWord {
  id: string;
  text: string;
  teeline_letters: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  topic: string;
  topic_name: string;
  is_curated: boolean;
  created_at: string;
}

export interface AdminJob {
  id: string;
  type: string;
  status: "pending" | "running" | "completed" | "failed" | "dead";
  priority: number;
  attempts: number;
  max_attempts: number;
  error_log: string;
  scheduled_at: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminJobDetail extends AdminJob {
  user: number | null;
  correlation_key: string | null;
  payload: Record<string, unknown>;
  locked_at: string | null;
  locked_by: string | null;
}

export interface AuditLogEntry {
  id: string;
  actor: number | null;
  actor_username: string | null;
  action: string;
  target_type: string;
  target_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface SystemSetting {
  id: string;
  key: string;
  value: unknown;
  updated_at: string;
  updated_by: number | null;
}

export interface UsageStats {
  daily: Array<{ date: string; count: number }>;
  total: number;
}

export interface RetentionStats {
  total_users: number;
  active_users: number;
  retention_rate: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

- [ ] **Step 3: Create admin API client**

Create `frontend/src/api/admin.ts`:

```typescript
import type {
  AdminUser,
  AdminJob,
  AdminJobDetail,
  AdminSymbol,
  AdminWord,
  AuditLogEntry,
  DashboardStats,
  PaginatedResponse,
  RetentionStats,
  SystemSetting,
  UsageStats,
} from "../types/admin";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

async function adminRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { getAccessToken } = await import("./client");
  const token = getAccessToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...(options.headers as Record<string, string>),
  };

  const response = await fetch(`${BASE_URL}/admin${path}`, { ...options, headers });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(`Admin API error ${response.status}: ${JSON.stringify(body)}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const adminApi = {
  dashboard: {
    stats(): Promise<DashboardStats> {
      return adminRequest("/dashboard/stats/");
    },
  },
  users: {
    list(params?: { search?: string; page?: number }): Promise<PaginatedResponse<AdminUser>> {
      const search = new URLSearchParams();
      if (params?.search) search.set("search", params.search);
      if (params?.page) search.set("page", String(params.page));
      const qs = search.toString();
      return adminRequest(`/users/${qs ? `?${qs}` : ""}`);
    },
    get(id: number): Promise<AdminUser> {
      return adminRequest(`/users/${id}/`);
    },
    update(id: number, data: Partial<Pick<AdminUser, "is_active" | "is_staff">>): Promise<AdminUser> {
      return adminRequest(`/users/${id}/`, { method: "PATCH", body: JSON.stringify(data) });
    },
  },
  content: {
    symbols: {
      list(): Promise<AdminSymbol[]> {
        return adminRequest("/content/symbols/");
      },
      create(data: { letter: string; name: string; reference_image_url?: string }): Promise<AdminSymbol> {
        return adminRequest("/content/symbols/", { method: "POST", body: JSON.stringify(data) });
      },
      update(id: number, data: Partial<AdminSymbol>): Promise<AdminSymbol> {
        return adminRequest(`/content/symbols/${id}/`, { method: "PATCH", body: JSON.stringify(data) });
      },
      delete(id: number): Promise<void> {
        return adminRequest(`/content/symbols/${id}/`, { method: "DELETE" });
      },
    },
    words: {
      list(): Promise<AdminWord[]> {
        return adminRequest("/content/words/");
      },
      create(data: Omit<AdminWord, "id" | "topic_name" | "created_at">): Promise<AdminWord> {
        return adminRequest("/content/words/", { method: "POST", body: JSON.stringify(data) });
      },
      update(id: string, data: Partial<AdminWord>): Promise<AdminWord> {
        return adminRequest(`/content/words/${id}/`, { method: "PATCH", body: JSON.stringify(data) });
      },
      delete(id: string): Promise<void> {
        return adminRequest(`/content/words/${id}/`, { method: "DELETE" });
      },
    },
  },
  analytics: {
    usage(days?: number): Promise<UsageStats> {
      const qs = days ? `?days=${days}` : "";
      return adminRequest(`/analytics/usage/${qs}`);
    },
    retention(days?: number): Promise<RetentionStats> {
      const qs = days ? `?days=${days}` : "";
      return adminRequest(`/analytics/retention/${qs}`);
    },
  },
  jobs: {
    list(params?: { status?: string; page?: number }): Promise<PaginatedResponse<AdminJob>> {
      const search = new URLSearchParams();
      if (params?.status) search.set("status", params.status);
      if (params?.page) search.set("page", String(params.page));
      const qs = search.toString();
      return adminRequest(`/jobs/${qs ? `?${qs}` : ""}`);
    },
    get(id: string): Promise<AdminJobDetail> {
      return adminRequest(`/jobs/${id}/`);
    },
    retry(id: string): Promise<AdminJob> {
      return adminRequest(`/jobs/${id}/retry/`, { method: "POST" });
    },
    cancel(id: string): Promise<AdminJob> {
      return adminRequest(`/jobs/${id}/cancel/`, { method: "POST" });
    },
  },
  auditLog: {
    list(params?: {
      action?: string;
      actor?: string;
      target_type?: string;
      page?: number;
    }): Promise<PaginatedResponse<AuditLogEntry>> {
      const search = new URLSearchParams();
      if (params?.action) search.set("action", params.action);
      if (params?.actor) search.set("actor", params.actor);
      if (params?.target_type) search.set("target_type", params.target_type);
      if (params?.page) search.set("page", String(params.page));
      const qs = search.toString();
      return adminRequest(`/audit-log/${qs ? `?${qs}` : ""}`);
    },
  },
  settings: {
    list(): Promise<SystemSetting[]> {
      return adminRequest("/settings/");
    },
    update(settings: Array<{ key: string; value: unknown }>): Promise<SystemSetting[]> {
      return adminRequest("/settings/", { method: "PATCH", body: JSON.stringify(settings) });
    },
  },
};
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/admin.ts frontend/src/api/admin.ts frontend/src/types/index.ts
git commit -m "feat(admin): add admin types and API client"
```

---

## Task 9: Admin Route Guard & Layout Shell

**Files:**
- Create: `frontend/src/components/admin/AdminRoute.tsx`
- Create: `frontend/src/pages/admin/AdminLayout.tsx`
- Create: `frontend/src/styles/admin.css`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create AdminRoute guard**

Create `frontend/src/components/admin/AdminRoute.tsx`:

```tsx
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api, getAccessToken } from "../../api/client";
import type { User } from "../../types";

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<"loading" | "allowed" | "denied">("loading");

  useEffect(() => {
    if (!getAccessToken()) {
      setState("denied");
      return;
    }
    api.auth
      .me()
      .then((user: User) => setState(user.is_staff ? "allowed" : "denied"))
      .catch(() => setState("denied"));
  }, []);

  if (state === "loading") {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <p style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</p>
      </div>
    );
  }

  if (state === "denied") {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
```

- [ ] **Step 2: Create admin CSS**

Create `frontend/src/styles/admin.css`:

```css
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: var(--paper);
}

.admin-sidebar {
  width: 220px;
  background: var(--ink);
  color: var(--paper);
  padding: 20px 0;
  flex-shrink: 0;
}

.admin-sidebar-logo {
  padding: 0 20px 20px;
  font-family: "Syne", sans-serif;
  font-size: 16px;
  font-weight: 700;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 12px;
}

.admin-sidebar-logo .accent {
  color: var(--accent);
}

.admin-nav {
  list-style: none;
  padding: 0;
  margin: 0;
}

.admin-nav a {
  display: block;
  padding: 10px 20px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 13px;
  font-family: "DM Mono", monospace;
  transition: background 0.15s, color 0.15s;
}

.admin-nav a:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--paper);
}

.admin-nav a.active {
  background: rgba(255, 255, 255, 0.1);
  color: var(--paper);
  border-left: 3px solid var(--accent);
  padding-left: 17px;
}

.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.admin-topbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--rule);
  font-size: 12px;
  font-family: "DM Mono", monospace;
  color: var(--muted);
}

.admin-topbar a {
  color: var(--muted);
  text-decoration: none;
}

.admin-topbar a:hover {
  color: var(--ink);
}

.admin-content {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
}

.admin-page-title {
  font-family: "Syne", sans-serif;
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--ink);
}

.admin-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.admin-stat-card {
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: 6px;
  padding: 16px;
}

.admin-stat-card .label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  font-family: "DM Mono", monospace;
  margin-bottom: 4px;
}

.admin-stat-card .value {
  font-family: "Syne", sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--ink);
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  font-family: "DM Mono", monospace;
}

.admin-table th {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 2px solid var(--rule);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
}

.admin-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--rule);
  color: var(--ink);
}

.admin-table tr:hover td {
  background: rgba(0, 0, 0, 0.02);
}

.admin-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.admin-badge.pending { background: #fef3c7; color: #92400e; }
.admin-badge.running { background: #dbeafe; color: #1e40af; }
.admin-badge.completed { background: #d1fae5; color: #065f46; }
.admin-badge.failed { background: #fee2e2; color: #991b1b; }
.admin-badge.dead { background: #f3f4f6; color: #6b7280; }

.admin-actions {
  display: flex;
  gap: 8px;
}

.admin-btn {
  padding: 6px 12px;
  font-size: 12px;
  font-family: "DM Mono", monospace;
  border: 1px solid var(--rule);
  border-radius: 4px;
  background: var(--paper);
  color: var(--ink);
  cursor: pointer;
  transition: background 0.15s;
}

.admin-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.admin-btn.danger {
  color: var(--accent);
  border-color: var(--accent);
}

.admin-btn.danger:hover {
  background: var(--accent);
  color: var(--paper);
}

.admin-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  font-size: 12px;
  font-family: "DM Mono", monospace;
  color: var(--muted);
}

.admin-search {
  padding: 8px 12px;
  font-size: 13px;
  font-family: "DM Mono", monospace;
  border: 1px solid var(--rule);
  border-radius: 4px;
  background: var(--paper);
  color: var(--ink);
  width: 300px;
  margin-bottom: 16px;
}

.admin-search:focus {
  outline: none;
  border-color: var(--ink);
}

.admin-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.admin-modal {
  background: var(--paper);
  border-radius: 8px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.admin-modal h3 {
  font-family: "Syne", sans-serif;
  font-size: 16px;
  margin-bottom: 8px;
}

.admin-modal p {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 16px;
}

.admin-modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
```

- [ ] **Step 3: Create AdminLayout**

Create `frontend/src/pages/admin/AdminLayout.tsx`:

```tsx
import { NavLink, Outlet } from "react-router-dom";
import { api } from "../../api/client";

const NAV_ITEMS = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/users", label: "Users" },
  { to: "/admin/content", label: "Content" },
  { to: "/admin/analytics", label: "Analytics" },
  { to: "/admin/jobs", label: "Jobs" },
  { to: "/admin/audit-log", label: "Audit Log" },
  { to: "/admin/settings", label: "Settings" },
];

export function AdminLayout() {
  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-sidebar-logo">
          Teeline <span className="accent">ML</span>
          <div style={{ fontSize: 10, opacity: 0.5, marginTop: 4 }}>Admin</div>
        </div>
        <nav className="admin-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="admin-main">
        <div className="admin-topbar">
          <a href="/">Back to app</a>
          <a
            href="#"
            onClick={async (e) => {
              e.preventDefault();
              await api.auth.logout();
              window.location.href = "/";
            }}
          >
            Logout
          </a>
        </div>
        <div className="admin-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Wire lazy-loaded admin routes into App.tsx**

Replace `frontend/src/App.tsx` with:

```tsx
import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./styles/tokens.css";
import "./styles/components.css";
import "./styles/layout.css";
import "./styles/admin.css";
import { Header } from "./components/Header";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { LoginPage } from "./pages/LoginPage";
import { PracticePage } from "./pages/PracticePage";
import { ProgressPage } from "./pages/ProgressPage";
import { WordPracticePage } from "./pages/WordPracticePage";
import { AdminRoute } from "./components/admin/AdminRoute";

const AdminLayout = lazy(() =>
  import("./pages/admin/AdminLayout").then((m) => ({ default: m.AdminLayout }))
);
const DashboardPage = lazy(() =>
  import("./pages/admin/DashboardPage").then((m) => ({ default: m.DashboardPage }))
);
const UsersPage = lazy(() =>
  import("./pages/admin/UsersPage").then((m) => ({ default: m.UsersPage }))
);
const UserDetailPage = lazy(() =>
  import("./pages/admin/UserDetailPage").then((m) => ({ default: m.UserDetailPage }))
);
const ContentPage = lazy(() =>
  import("./pages/admin/ContentPage").then((m) => ({ default: m.ContentPage }))
);
const AnalyticsPage = lazy(() =>
  import("./pages/admin/AnalyticsPage").then((m) => ({ default: m.AnalyticsPage }))
);
const JobsPage = lazy(() =>
  import("./pages/admin/JobsPage").then((m) => ({ default: m.JobsPage }))
);
const AuditLogPage = lazy(() =>
  import("./pages/admin/AuditLogPage").then((m) => ({ default: m.AuditLogPage }))
);
const SettingsPage = lazy(() =>
  import("./pages/admin/SettingsPage").then((m) => ({ default: m.SettingsPage }))
);

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/admin/*"
          element={
            <AdminRoute>
              <Suspense fallback={<div style={{ padding: 24 }}>Loading...</div>}>
                <Routes>
                  <Route element={<AdminLayout />}>
                    <Route index element={<DashboardPage />} />
                    <Route path="users" element={<UsersPage />} />
                    <Route path="users/:id" element={<UserDetailPage />} />
                    <Route path="content" element={<ContentPage />} />
                    <Route path="analytics" element={<AnalyticsPage />} />
                    <Route path="jobs" element={<JobsPage />} />
                    <Route path="audit-log" element={<AuditLogPage />} />
                    <Route path="settings" element={<SettingsPage />} />
                  </Route>
                </Routes>
              </Suspense>
            </AdminRoute>
          }
        />
        <Route
          path="*"
          element={
            <>
              <Header />
              <Routes>
                <Route path="/" element={<PracticePage />} />
                <Route path="/words" element={<WordPracticePage />} />
                <Route path="/progress" element={<ProgressPage />} />
                <Route path="/leaderboard" element={<LeaderboardPage />} />
                <Route path="/login" element={<LoginPage />} />
              </Routes>
            </>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 5: Verify TypeScript compiles**

Note: this will fail because the admin page components don't exist yet. That's expected — we'll create stub pages in the next task. For now, just verify the AdminRoute, AdminLayout, and admin.css have no issues by checking those files specifically:

```bash
cd frontend && npx tsc --noEmit src/components/admin/AdminRoute.tsx src/pages/admin/AdminLayout.tsx 2>&1 || true
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/admin/AdminRoute.tsx frontend/src/pages/admin/AdminLayout.tsx frontend/src/styles/admin.css frontend/src/App.tsx
git commit -m "feat(admin): add AdminRoute guard, AdminLayout shell, and admin CSS"
```

---

## Task 10: Admin Page Components — Dashboard & Users

**Files:**
- Create: `frontend/src/pages/admin/DashboardPage.tsx`
- Create: `frontend/src/pages/admin/UsersPage.tsx`
- Create: `frontend/src/pages/admin/UserDetailPage.tsx`
- Create: `frontend/src/components/admin/StatCard.tsx`
- Create: `frontend/src/components/admin/ActionConfirm.tsx`

- [ ] **Step 1: Create StatCard component**

Create `frontend/src/components/admin/StatCard.tsx`:

```tsx
export function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="admin-stat-card">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}
```

- [ ] **Step 2: Create ActionConfirm modal**

Create `frontend/src/components/admin/ActionConfirm.tsx`:

```tsx
export function ActionConfirm({
  title,
  message,
  confirmLabel,
  onConfirm,
  onCancel,
}: {
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="admin-modal-overlay" onClick={onCancel}>
      <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="admin-modal-actions">
          <button className="admin-btn" onClick={onCancel}>Cancel</button>
          <button className="admin-btn danger" onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create DashboardPage**

Create `frontend/src/pages/admin/DashboardPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import { StatCard } from "../../components/admin/StatCard";
import type { DashboardStats } from "../../types/admin";

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminApi.dashboard
      .stats()
      .then(setStats)
      .catch(() => setError("Failed to load dashboard stats"));
  }, []);

  if (error) return <p style={{ color: "var(--accent)" }}>{error}</p>;
  if (!stats) return <p style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</p>;

  return (
    <div>
      <h1 className="admin-page-title">Dashboard</h1>
      <div className="admin-stats-grid">
        <StatCard label="Total Users" value={stats.user_count} />
        <StatCard label="Total Attempts" value={stats.attempt_count} />
        <StatCard label="Active Today" value={stats.active_today} />
        <StatCard label="Pending Jobs" value={stats.pending_jobs} />
        <StatCard label="Failed Jobs" value={stats.failed_jobs} />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create UsersPage**

Create `frontend/src/pages/admin/UsersPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "../../api/admin";
import type { AdminUser, PaginatedResponse } from "../../types/admin";

export function UsersPage() {
  const [data, setData] = useState<PaginatedResponse<AdminUser> | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminApi.users
      .list({ search: search || undefined, page })
      .then(setData)
      .catch(() => setError("Failed to load users"));
  }, [search, page]);

  return (
    <div>
      <h1 className="admin-page-title">Users</h1>
      <input
        className="admin-search"
        placeholder="Search by username or email..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
      />
      {error && <p style={{ color: "var(--accent)" }}>{error}</p>}
      {data && (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Staff</th>
                <th>Active</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((user) => (
                <tr key={user.id}>
                  <td>
                    <Link to={`/admin/users/${user.id}`} style={{ color: "var(--ink)" }}>
                      {user.username}
                    </Link>
                  </td>
                  <td>{user.email}</td>
                  <td>{user.is_staff ? "Yes" : "No"}</td>
                  <td>{user.is_active ? "Yes" : "No"}</td>
                  <td>{new Date(user.date_joined).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="admin-pagination">
            <button
              className="admin-btn"
              disabled={!data.previous}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span>Page {page}</span>
            <button
              className="admin-btn"
              disabled={!data.next}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Create UserDetailPage**

Create `frontend/src/pages/admin/UserDetailPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { adminApi } from "../../api/admin";
import { ActionConfirm } from "../../components/admin/ActionConfirm";
import type { AdminUser } from "../../types/admin";

export function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [user, setUser] = useState<AdminUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<{ action: string; field: string; value: boolean } | null>(null);

  useEffect(() => {
    if (!id) return;
    adminApi.users
      .get(Number(id))
      .then(setUser)
      .catch(() => setError("Failed to load user"));
  }, [id]);

  const handleToggle = async (field: "is_active" | "is_staff", value: boolean) => {
    if (!id) return;
    try {
      const updated = await adminApi.users.update(Number(id), { [field]: value });
      setUser(updated);
      setConfirm(null);
    } catch {
      setError("Failed to update user");
    }
  };

  if (error) return <p style={{ color: "var(--accent)" }}>{error}</p>;
  if (!user) return <p style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</p>;

  return (
    <div>
      <button className="admin-btn" onClick={() => navigate("/admin/users")} style={{ marginBottom: 16 }}>
        Back to Users
      </button>
      <h1 className="admin-page-title">{user.username}</h1>
      <table className="admin-table" style={{ maxWidth: 500 }}>
        <tbody>
          <tr><td>Email</td><td>{user.email}</td></tr>
          <tr><td>Joined</td><td>{new Date(user.date_joined).toLocaleDateString()}</td></tr>
          <tr><td>Last Login</td><td>{user.last_login ? new Date(user.last_login).toLocaleString() : "Never"}</td></tr>
          <tr>
            <td>Active</td>
            <td>
              <button
                className={`admin-btn ${user.is_active ? "danger" : ""}`}
                onClick={() =>
                  setConfirm({
                    action: user.is_active ? "Deactivate" : "Activate",
                    field: "is_active",
                    value: !user.is_active,
                  })
                }
              >
                {user.is_active ? "Deactivate" : "Activate"}
              </button>
            </td>
          </tr>
          <tr>
            <td>Admin</td>
            <td>
              <button
                className={`admin-btn ${user.is_staff ? "danger" : ""}`}
                onClick={() =>
                  setConfirm({
                    action: user.is_staff ? "Remove admin" : "Make admin",
                    field: "is_staff",
                    value: !user.is_staff,
                  })
                }
              >
                {user.is_staff ? "Remove admin" : "Make admin"}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      {confirm && (
        <ActionConfirm
          title={`${confirm.action} user`}
          message={`Are you sure you want to ${confirm.action.toLowerCase()} ${user.username}?`}
          confirmLabel={confirm.action}
          onConfirm={() => handleToggle(confirm.field as "is_active" | "is_staff", confirm.value)}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/admin/StatCard.tsx frontend/src/components/admin/ActionConfirm.tsx frontend/src/pages/admin/DashboardPage.tsx frontend/src/pages/admin/UsersPage.tsx frontend/src/pages/admin/UserDetailPage.tsx
git commit -m "feat(admin): add Dashboard, Users, and UserDetail pages"
```

---

## Task 11: Admin Page Components — Content, Analytics, Jobs, Audit Log, Settings

**Files:**
- Create: `frontend/src/pages/admin/ContentPage.tsx`
- Create: `frontend/src/pages/admin/AnalyticsPage.tsx`
- Create: `frontend/src/pages/admin/JobsPage.tsx`
- Create: `frontend/src/pages/admin/AuditLogPage.tsx`
- Create: `frontend/src/pages/admin/SettingsPage.tsx`

- [ ] **Step 1: Create ContentPage**

Create `frontend/src/pages/admin/ContentPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import { ActionConfirm } from "../../components/admin/ActionConfirm";
import type { AdminSymbol, AdminWord } from "../../types/admin";

export function ContentPage() {
  const [symbols, setSymbols] = useState<AdminSymbol[]>([]);
  const [words, setWords] = useState<AdminWord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<{ type: "symbol" | "word"; id: number | string; name: string } | null>(null);

  const loadData = () => {
    Promise.all([adminApi.content.symbols.list(), adminApi.content.words.list()])
      .then(([s, w]) => { setSymbols(s); setWords(w); })
      .catch(() => setError("Failed to load content"));
  };

  useEffect(loadData, []);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (deleteTarget.type === "symbol") {
        await adminApi.content.symbols.delete(deleteTarget.id as number);
      } else {
        await adminApi.content.words.delete(deleteTarget.id as string);
      }
      setDeleteTarget(null);
      loadData();
    } catch {
      setError("Failed to delete");
    }
  };

  return (
    <div>
      <h1 className="admin-page-title">Content</h1>
      {error && <p style={{ color: "var(--accent)" }}>{error}</p>}

      <h2 style={{ fontFamily: "'Syne', sans-serif", fontSize: 16, marginBottom: 12 }}>
        Symbols ({symbols.length})
      </h2>
      <table className="admin-table" style={{ marginBottom: 32 }}>
        <thead>
          <tr>
            <th>Letter</th>
            <th>Name</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {symbols.map((s) => (
            <tr key={s.id}>
              <td>{s.letter}</td>
              <td>{s.name}</td>
              <td>
                <button
                  className="admin-btn danger"
                  onClick={() => setDeleteTarget({ type: "symbol", id: s.id, name: s.letter })}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 style={{ fontFamily: "'Syne', sans-serif", fontSize: 16, marginBottom: 12 }}>
        Words ({words.length})
      </h2>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Text</th>
            <th>Teeline</th>
            <th>Difficulty</th>
            <th>Topic</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {words.map((w) => (
            <tr key={w.id}>
              <td>{w.text}</td>
              <td>{w.teeline_letters}</td>
              <td>{w.difficulty}</td>
              <td>{w.topic_name}</td>
              <td>
                <button
                  className="admin-btn danger"
                  onClick={() => setDeleteTarget({ type: "word", id: w.id, name: w.text })}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {deleteTarget && (
        <ActionConfirm
          title={`Delete ${deleteTarget.type}`}
          message={`Are you sure you want to delete "${deleteTarget.name}"? This cannot be undone.`}
          confirmLabel="Delete"
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create AnalyticsPage**

Create `frontend/src/pages/admin/AnalyticsPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import { StatCard } from "../../components/admin/StatCard";
import type { RetentionStats, UsageStats } from "../../types/admin";

export function AnalyticsPage() {
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [retention, setRetention] = useState<RetentionStats | null>(null);
  const [days, setDays] = useState(30);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([adminApi.analytics.usage(days), adminApi.analytics.retention(days)])
      .then(([u, r]) => { setUsage(u); setRetention(r); })
      .catch(() => setError("Failed to load analytics"));
  }, [days]);

  if (error) return <p style={{ color: "var(--accent)" }}>{error}</p>;
  if (!usage || !retention) return <p style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</p>;

  return (
    <div>
      <h1 className="admin-page-title">Analytics</h1>
      <div style={{ marginBottom: 16 }}>
        <select
          className="admin-search"
          style={{ width: "auto" }}
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>
      <div className="admin-stats-grid">
        <StatCard label="Total Attempts" value={usage.total} />
        <StatCard label="Total Users" value={retention.total_users} />
        <StatCard label="Active Users" value={retention.active_users} />
        <StatCard label="Retention Rate" value={`${retention.retention_rate}%`} />
      </div>

      <h2 style={{ fontFamily: "'Syne', sans-serif", fontSize: 16, margin: "24px 0 12px" }}>
        Daily Attempts
      </h2>
      <table className="admin-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Attempts</th>
          </tr>
        </thead>
        <tbody>
          {usage.daily.map((row) => (
            <tr key={row.date}>
              <td>{row.date}</td>
              <td>{row.count}</td>
            </tr>
          ))}
          {usage.daily.length === 0 && (
            <tr><td colSpan={2} style={{ textAlign: "center", color: "var(--muted)" }}>No data</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 3: Create JobsPage**

Create `frontend/src/pages/admin/JobsPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import { ActionConfirm } from "../../components/admin/ActionConfirm";
import type { AdminJob, PaginatedResponse } from "../../types/admin";

export function JobsPage() {
  const [data, setData] = useState<PaginatedResponse<AdminJob> | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<{ type: "retry" | "cancel"; job: AdminJob } | null>(null);

  const loadJobs = () => {
    adminApi.jobs
      .list({ status: statusFilter || undefined, page })
      .then(setData)
      .catch(() => setError("Failed to load jobs"));
  };

  useEffect(loadJobs, [statusFilter, page]);

  const handleAction = async () => {
    if (!action) return;
    try {
      if (action.type === "retry") {
        await adminApi.jobs.retry(action.job.id);
      } else {
        await adminApi.jobs.cancel(action.job.id);
      }
      setAction(null);
      loadJobs();
    } catch {
      setError(`Failed to ${action.type} job`);
    }
  };

  return (
    <div>
      <h1 className="admin-page-title">Jobs</h1>
      <select
        className="admin-search"
        style={{ width: "auto" }}
        value={statusFilter}
        onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
      >
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="running">Running</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
        <option value="dead">Dead</option>
      </select>
      {error && <p style={{ color: "var(--accent)" }}>{error}</p>}
      {data && (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Status</th>
                <th>Attempts</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((job) => (
                <tr key={job.id}>
                  <td>{job.type}</td>
                  <td><span className={`admin-badge ${job.status}`}>{job.status}</span></td>
                  <td>{job.attempts}/{job.max_attempts}</td>
                  <td>{new Date(job.created_at).toLocaleString()}</td>
                  <td className="admin-actions">
                    {(job.status === "failed" || job.status === "dead") && (
                      <button className="admin-btn" onClick={() => setAction({ type: "retry", job })}>
                        Retry
                      </button>
                    )}
                    {job.status === "pending" && (
                      <button className="admin-btn danger" onClick={() => setAction({ type: "cancel", job })}>
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="admin-pagination">
            <button className="admin-btn" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>Previous</button>
            <span>Page {page}</span>
            <button className="admin-btn" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>Next</button>
          </div>
        </>
      )}

      {action && (
        <ActionConfirm
          title={`${action.type === "retry" ? "Retry" : "Cancel"} job`}
          message={`Are you sure you want to ${action.type} job "${action.job.type}" (${action.job.id.slice(0, 8)}...)?`}
          confirmLabel={action.type === "retry" ? "Retry" : "Cancel Job"}
          onConfirm={handleAction}
          onCancel={() => setAction(null)}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 4: Create AuditLogPage**

Create `frontend/src/pages/admin/AuditLogPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import type { AuditLogEntry, PaginatedResponse } from "../../types/admin";

export function AuditLogPage() {
  const [data, setData] = useState<PaginatedResponse<AuditLogEntry> | null>(null);
  const [actionFilter, setActionFilter] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminApi.auditLog
      .list({ action: actionFilter || undefined, page })
      .then(setData)
      .catch(() => setError("Failed to load audit log"));
  }, [actionFilter, page]);

  return (
    <div>
      <h1 className="admin-page-title">Audit Log</h1>
      <input
        className="admin-search"
        placeholder="Filter by action (e.g. user.update)..."
        value={actionFilter}
        onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
      />
      {error && <p style={{ color: "var(--accent)" }}>{error}</p>}
      {data && (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((entry) => (
                <tr key={entry.id}>
                  <td>{new Date(entry.created_at).toLocaleString()}</td>
                  <td>{entry.actor_username || "System"}</td>
                  <td><code style={{ fontSize: 11 }}>{entry.action}</code></td>
                  <td>{entry.target_type}:{entry.target_id.slice(0, 8)}</td>
                  <td>
                    <details>
                      <summary style={{ cursor: "pointer", fontSize: 11, color: "var(--muted)" }}>View</summary>
                      <pre style={{ fontSize: 10, maxWidth: 400, overflow: "auto", marginTop: 4 }}>
                        {JSON.stringify(entry.details, null, 2)}
                      </pre>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="admin-pagination">
            <button className="admin-btn" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>Previous</button>
            <span>Page {page}</span>
            <button className="admin-btn" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>Next</button>
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Create SettingsPage**

Create `frontend/src/pages/admin/SettingsPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import type { SystemSetting } from "../../types/admin";

export function SettingsPage() {
  const [settings, setSettings] = useState<SystemSetting[]>([]);
  const [edited, setEdited] = useState<Record<string, unknown>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    adminApi.settings
      .list()
      .then(setSettings)
      .catch(() => setError("Failed to load settings"));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const updates = Object.entries(edited).map(([key, value]) => ({ key, value }));
      const updated = await adminApi.settings.update(updates);
      setSettings(updated);
      setEdited({});
      setSuccess(true);
    } catch {
      setError("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const hasChanges = Object.keys(edited).length > 0;

  return (
    <div>
      <h1 className="admin-page-title">Settings</h1>
      {error && <p style={{ color: "var(--accent)", marginBottom: 12 }}>{error}</p>}
      {success && <p style={{ color: "#065f46", marginBottom: 12 }}>Settings saved.</p>}

      {settings.length === 0 && !error && (
        <p style={{ color: "var(--muted)", fontSize: 12 }}>
          No settings configured. Use Django shell to create SystemSetting entries.
        </p>
      )}

      {settings.length > 0 && (
        <>
          <table className="admin-table" style={{ maxWidth: 600 }}>
            <thead>
              <tr>
                <th>Key</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {settings.map((s) => (
                <tr key={s.key}>
                  <td><code style={{ fontSize: 12 }}>{s.key}</code></td>
                  <td>
                    {typeof s.value === "boolean" ? (
                      <button
                        className="admin-btn"
                        onClick={() => {
                          const current = edited[s.key] ?? s.value;
                          setEdited({ ...edited, [s.key]: !current });
                        }}
                      >
                        {String(edited[s.key] ?? s.value)}
                      </button>
                    ) : (
                      <input
                        className="admin-search"
                        style={{ width: "auto", marginBottom: 0 }}
                        value={String(edited[s.key] ?? s.value)}
                        onChange={(e) => setEdited({ ...edited, [s.key]: e.target.value })}
                      />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {hasChanges && (
            <button
              className="admin-btn"
              style={{ marginTop: 12 }}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? "Saving..." : "Save Changes"}
            </button>
          )}
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/admin/ContentPage.tsx frontend/src/pages/admin/AnalyticsPage.tsx frontend/src/pages/admin/JobsPage.tsx frontend/src/pages/admin/AuditLogPage.tsx frontend/src/pages/admin/SettingsPage.tsx
git commit -m "feat(admin): add Content, Analytics, Jobs, AuditLog, and Settings pages"
```

---

## Task 12: Integration Test & Visual Verification

**Files:** None (testing only)

- [ ] **Step 1: Run full backend tests**

```bash
cd backend && python manage.py test -v2
```

Expected: all tests pass including existing and new admin tests.

- [ ] **Step 2: Run frontend build**

```bash
cd frontend && npx tsc --noEmit && npm run build
```

Expected: TypeScript compiles with no errors. Vite build succeeds. Admin pages are split into a separate chunk.

- [ ] **Step 3: Create a test admin user**

```bash
cd backend && python manage.py make_admin <your-username>
```

Or if no user exists yet:

```bash
cd backend && python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.create_user('admin', 'admin@test.com', 'testpass1234')
u.is_staff = True
u.save()
print(f'Created admin user: {u.username}')
"
```

- [ ] **Step 4: Start dev servers and verify in browser**

```bash
# Terminal 1: backend
cd backend && python manage.py runserver

# Terminal 2: frontend
cd frontend && npm run dev
```

Verify:
1. Navigate to `/admin` — should show dashboard with stats
2. Click through each sidebar link — each page should load
3. Navigate to `/admin` while logged out — should redirect to `/`
4. Navigate to `/` — main app should work normally with no admin UI visible
5. Check that admin pages lazy-load (Network tab shows separate chunk)

- [ ] **Step 5: Commit any fixes if needed**

```bash
git add -A && git commit -m "fix(admin): integration fixes from manual testing"
```

Only commit if there were actual fixes. Skip if everything worked.

- [ ] **Step 6: Final commit — tag feature complete**

```bash
git add -A && git commit -m "feat(admin): admin panel complete with RBAC, dashboard, CRUD, jobs, audit log, and settings"
```

Only if there are uncommitted changes. Otherwise skip.
