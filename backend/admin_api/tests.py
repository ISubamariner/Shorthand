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
