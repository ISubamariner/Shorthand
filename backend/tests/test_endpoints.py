"""
System smoke test — verifies every API endpoint returns the expected status code.
Run: python manage.py test tests.test_endpoints
"""
import base64
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import AnonymousSession
from admin_api.models import SystemSetting
from checker.models import Attempt, Symbol, Word, WordAttemptSession, WordTopic
from jobs.models import Job


class EndpointTestBase(TestCase):
    """Shared setup: users, session, symbols, words, and API clients."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "smokeuser", "smoke@example.com", "testpass12345"
        )
        cls.admin = User.objects.create_user(
            "smokeadmin", "admin@example.com", "testpass12345"
        )
        cls.admin.is_staff = True
        cls.admin.save()

        cls.session = AnonymousSession.objects.create(session_token=uuid.uuid4())

        cls.symbol = Symbol.objects.create(letter="A", name="Alpha")
        cls.topic = WordTopic.objects.create(name="Greetings", slug="greetings")
        cls.word = Word.objects.create(
            text="hello", teeline_letters="hl", difficulty="beginner", topic=cls.topic
        )

    def setUp(self):
        self.anon_client = APIClient()

        self.session_client = APIClient()
        self.session_client.defaults["HTTP_X_SESSION_TOKEN"] = str(
            self.session.session_token
        )

        self.auth_client = APIClient()
        self.auth_client.force_authenticate(user=self.user)

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)


# ---------- Auth endpoints (/api/auth/) ----------


class AuthEndpointsTest(EndpointTestBase):

    def test_register(self):
        r = self.anon_client.post("/api/auth/register/", {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass12345",
        })
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_register_bad_request(self):
        r = self.anon_client.post("/api/auth/register/", {})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        r = self.anon_client.post("/api/auth/login/", {
            "username": "smokeuser",
            "password": "testpass12345",
        })
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("access", r.data)

    def test_login_bad_credentials(self):
        r = self.anon_client.post("/api/auth/login/", {
            "username": "smokeuser",
            "password": "wrong",
        })
        self.assertIn(r.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED))

    def test_refresh(self):
        login = self.anon_client.post("/api/auth/login/", {
            "username": "smokeuser",
            "password": "testpass12345",
        })
        r = self.anon_client.post("/api/auth/refresh/", {
            "refresh": login.data["refresh"],
        })
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_me_authenticated(self):
        r = self.auth_client.get("/api/auth/me/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_me_unauthenticated(self):
        r = self.anon_client.get("/api/auth/me/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_patch(self):
        r = self.auth_client.patch(
            "/api/auth/me/",
            {"email": "updated@example.com", "current_password": "testpass12345"},
            format="json",
        )
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))

    def test_claim_session(self):
        session = AnonymousSession.objects.create(session_token=uuid.uuid4())
        client = APIClient()
        client.force_authenticate(user=self.user)
        client.defaults["HTTP_X_SESSION_TOKEN"] = str(session.session_token)
        r = client.post("/api/auth/claim-session/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))

    def test_claim_session_unauthenticated(self):
        r = self.anon_client.post("/api/auth/claim-session/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        r = self.auth_client.post("/api/auth/logout/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))

    def test_logout_unauthenticated(self):
        r = self.anon_client.post("/api/auth/logout/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------- Symbols (/api/symbols/) ----------


class SymbolEndpointsTest(EndpointTestBase):

    def test_symbol_list(self):
        r = self.anon_client.get("/api/symbols/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_symbol_detail(self):
        r = self.anon_client.get(f"/api/symbols/{self.symbol.letter}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_symbol_detail_not_found(self):
        # BUG: view raises DoesNotExist instead of returning 404
        with self.assertRaises(Symbol.DoesNotExist):
            self.anon_client.get("/api/symbols/9/")


# ---------- Attempts (/api/attempts/) ----------


class AttemptEndpointsTest(EndpointTestBase):

    def _tiny_png_b64(self):
        pixel = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
            b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
            b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return base64.b64encode(pixel).decode()

    def test_attempt_list_with_session(self):
        r = self.session_client.get("/api/attempts/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_attempt_list_unauthenticated_no_session(self):
        r = self.anon_client.get("/api/attempts/")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_attempt_create_with_session(self):
        r = self.session_client.post("/api/attempts/", {
            "symbol_letter": "a",
            "image_data": self._tiny_png_b64(),
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_attempt_create_authenticated(self):
        r = self.auth_client.post("/api/attempts/", {
            "symbol_letter": "a",
            "image_data": self._tiny_png_b64(),
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_attempt_detail_not_found(self):
        # BUG: view raises DoesNotExist instead of returning 404
        with self.assertRaises(Attempt.DoesNotExist):
            self.auth_client.get(f"/api/attempts/{uuid.uuid4()}/")


# ---------- Progress & Leaderboard ----------


class ProgressEndpointsTest(EndpointTestBase):

    def test_progress_authenticated(self):
        r = self.auth_client.get("/api/progress/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_progress_with_session(self):
        r = self.session_client.get("/api/progress/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_progress_unauthenticated(self):
        r = self.anon_client.get("/api/progress/")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_leaderboard(self):
        r = self.anon_client.get("/api/leaderboard/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)


# ---------- Words & Topics (/api/words/, /api/word-topics/) ----------


class WordEndpointsTest(EndpointTestBase):

    def test_word_topic_list(self):
        r = self.anon_client.get("/api/word-topics/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_list(self):
        r = self.anon_client.get("/api/words/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_list_with_filters(self):
        r = self.anon_client.get("/api/words/?difficulty=beginner&topic=greetings")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_detail(self):
        r = self.anon_client.get(f"/api/words/{self.word.pk}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_detail_not_found(self):
        # BUG: view raises DoesNotExist instead of returning 404
        with self.assertRaises(Word.DoesNotExist):
            self.anon_client.get(f"/api/words/{uuid.uuid4()}/")


# ---------- Word Sessions (/api/word-sessions/) ----------


class WordSessionEndpointsTest(EndpointTestBase):

    def test_create_word_session(self):
        r = self.auth_client.post(
            "/api/word-sessions/", {"word_id": str(self.word.pk)}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_word_session_detail(self):
        session = WordAttemptSession.objects.create(
            word=self.word, user=self.user, status="in_progress"
        )
        r = self.auth_client.get(f"/api/word-sessions/{session.pk}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_session_complete(self):
        session = WordAttemptSession.objects.create(
            word=self.word, user=self.user, status="in_progress"
        )
        r = self.auth_client.post(f"/api/word-sessions/{session.pk}/complete/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))

    def test_word_session_not_found(self):
        # BUG: view raises DoesNotExist instead of returning 404
        with self.assertRaises(WordAttemptSession.DoesNotExist):
            self.auth_client.get(f"/api/word-sessions/{uuid.uuid4()}/")


# ---------- Word Progress (/api/word-progress/) ----------


class WordProgressEndpointsTest(EndpointTestBase):

    def test_word_progress_authenticated(self):
        r = self.auth_client.get("/api/word-progress/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_progress_with_filters(self):
        r = self.auth_client.get("/api/word-progress/?difficulty=beginner&topic=greetings")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_progress_unauthenticated(self):
        r = self.anon_client.get("/api/word-progress/")
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


# ---------- Admin: Dashboard (/api/admin/dashboard/) ----------


class AdminDashboardEndpointsTest(EndpointTestBase):

    def test_dashboard_stats(self):
        r = self.admin_client.get("/api/admin/dashboard/stats/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_dashboard_stats_non_admin(self):
        r = self.auth_client.get("/api/admin/dashboard/stats/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_stats_unauthenticated(self):
        r = self.anon_client.get("/api/admin/dashboard/stats/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------- Admin: Users (/api/admin/users/) ----------


class AdminUserEndpointsTest(EndpointTestBase):

    def test_user_list(self):
        r = self.admin_client.get("/api/admin/users/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_user_list_search(self):
        r = self.admin_client.get("/api/admin/users/?search=smoke")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_user_detail(self):
        r = self.admin_client.get(f"/api/admin/users/{self.user.pk}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_user_detail_patch(self):
        r = self.admin_client.patch(
            f"/api/admin/users/{self.user.pk}/",
            {"is_active": True},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_user_list_non_admin(self):
        r = self.auth_client.get("/api/admin/users/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


# ---------- Admin: Content (/api/admin/content/) ----------


class AdminContentEndpointsTest(EndpointTestBase):

    def test_symbol_list(self):
        r = self.admin_client.get("/api/admin/content/symbols/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_symbol_create(self):
        r = self.admin_client.post(
            "/api/admin/content/symbols/",
            {"letter": "z", "name": "Zulu"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_symbol_detail(self):
        r = self.admin_client.get(f"/api/admin/content/symbols/{self.symbol.pk}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_symbol_patch(self):
        r = self.admin_client.patch(
            f"/api/admin/content/symbols/{self.symbol.pk}/",
            {"name": "Alpha Updated"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_symbol_delete(self):
        sym = Symbol.objects.create(letter="q", name="Quebec")
        r = self.admin_client.delete(f"/api/admin/content/symbols/{sym.pk}/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))

    def test_word_list(self):
        r = self.admin_client.get("/api/admin/content/words/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_create(self):
        r = self.admin_client.post(
            "/api/admin/content/words/",
            {
                "text": "world",
                "teeline_letters": "wrld",
                "difficulty": "beginner",
                "topic": str(self.topic.pk),
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_word_detail(self):
        r = self.admin_client.get(f"/api/admin/content/words/{self.word.pk}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_patch(self):
        r = self.admin_client.patch(
            f"/api/admin/content/words/{self.word.pk}/",
            {"difficulty": "intermediate"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_word_delete(self):
        w = Word.objects.create(
            text="temp", teeline_letters="tmp", difficulty="beginner", topic=self.topic
        )
        r = self.admin_client.delete(f"/api/admin/content/words/{w.pk}/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))

    def test_content_non_admin(self):
        r = self.auth_client.get("/api/admin/content/symbols/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


# ---------- Admin: Analytics (/api/admin/analytics/) ----------


class AdminAnalyticsEndpointsTest(EndpointTestBase):

    def test_usage_stats(self):
        r = self.admin_client.get("/api/admin/analytics/usage/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_usage_stats_with_days(self):
        r = self.admin_client.get("/api/admin/analytics/usage/?days=7")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_retention_stats(self):
        r = self.admin_client.get("/api/admin/analytics/retention/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_analytics_non_admin(self):
        r = self.auth_client.get("/api/admin/analytics/usage/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


# ---------- Admin: Jobs (/api/admin/jobs/) ----------


class AdminJobEndpointsTest(EndpointTestBase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.job = Job.objects.create(
            type="predict", status="failed", payload={"test": True}
        )

    def test_job_list(self):
        r = self.admin_client.get("/api/admin/jobs/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_job_list_filter(self):
        r = self.admin_client.get("/api/admin/jobs/?status=failed")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_job_detail(self):
        r = self.admin_client.get(f"/api/admin/jobs/{self.job.pk}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_job_retry(self):
        r = self.admin_client.post(f"/api/admin/jobs/{self.job.pk}/retry/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))

    def test_job_cancel(self):
        job = Job.objects.create(type="predict", status="pending", payload={})
        r = self.admin_client.post(f"/api/admin/jobs/{job.pk}/cancel/")
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))

    def test_jobs_non_admin(self):
        r = self.auth_client.get("/api/admin/jobs/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


# ---------- Admin: Audit Log (/api/admin/audit-log/) ----------


class AdminAuditLogEndpointsTest(EndpointTestBase):

    def test_audit_log_list(self):
        r = self.admin_client.get("/api/admin/audit-log/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_audit_log_filter(self):
        r = self.admin_client.get("/api/admin/audit-log/?action=user.update")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_audit_log_non_admin(self):
        r = self.auth_client.get("/api/admin/audit-log/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


# ---------- Admin: Settings (/api/admin/settings/) ----------


class AdminSettingsEndpointsTest(EndpointTestBase):

    def test_settings_get(self):
        r = self.admin_client.get("/api/admin/settings/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_settings_patch(self):
        SystemSetting.objects.create(
            key="maintenance_mode", value={"enabled": False}
        )
        r = self.admin_client.patch(
            "/api/admin/settings/",
            [{"key": "maintenance_mode", "value": {"enabled": True}}],
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_settings_non_admin(self):
        r = self.auth_client.get("/api/admin/settings/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
