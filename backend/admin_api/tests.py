from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from admin_api.models import AuditLog
from admin_api.permissions import IsAdminUser
from admin_api.services import log_audit
from jobs.models import Job


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


from checker.models import Symbol, Word, WordTopic


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
