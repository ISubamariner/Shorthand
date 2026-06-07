from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class CollectorServerMetricsTest(TestCase):

    @patch("monitoring.collector.psutil")
    def test_collect_server_metrics_returns_expected_keys(self, mock_psutil):
        mock_psutil.cpu_percent.return_value = 42.5
        mem = MagicMock()
        mem.percent = 65.0
        mem.used = 4 * 1024 * 1024 * 1024
        mem.total = 16 * 1024 * 1024 * 1024
        mock_psutil.virtual_memory.return_value = mem
        disk = MagicMock()
        disk.percent = 55.0
        disk.used = 100 * 1024 * 1024 * 1024
        disk.total = 500 * 1024 * 1024 * 1024
        mock_psutil.disk_usage.return_value = disk

        from monitoring.collector import collect_server_metrics

        result = collect_server_metrics()

        self.assertAlmostEqual(result["cpu_percent"], 42.5)
        self.assertAlmostEqual(result["memory_percent"], 65.0)
        self.assertAlmostEqual(result["memory_used_mb"], 4096.0)
        self.assertAlmostEqual(result["memory_total_mb"], 16384.0)
        self.assertAlmostEqual(result["disk_percent"], 55.0)
        self.assertAlmostEqual(result["disk_used_gb"], 100.0)
        self.assertAlmostEqual(result["disk_total_gb"], 500.0)
        self.assertIn("process_uptime_seconds", result)
        self.assertGreater(result["process_uptime_seconds"], 0)


class CollectorDbMetricsTest(TestCase):

    def test_returns_zeros_on_non_postgresql(self):
        from monitoring.collector import collect_db_metrics

        result = collect_db_metrics()
        self.assertEqual(result["db_size_mb"], 0)
        self.assertEqual(result["db_connections"], 0)
        self.assertEqual(result["table_stats"], [])


class CollectorSnapshotTest(TestCase):

    @patch("monitoring.collector.collect_db_metrics")
    @patch("monitoring.collector.collect_server_metrics")
    def test_collect_snapshot_combines_server_and_db(self, mock_server, mock_db):
        mock_server.return_value = {
            "cpu_percent": 10.0,
            "memory_percent": 20.0,
            "memory_used_mb": 2048.0,
            "memory_total_mb": 8192.0,
            "disk_percent": 30.0,
            "disk_used_gb": 50.0,
            "disk_total_gb": 200.0,
            "process_uptime_seconds": 3600.0,
        }
        mock_db.return_value = {
            "db_size_mb": 150.5,
            "db_connections": 5,
            "table_stats": [{"name": "auth_user", "row_count": 10, "size_mb": 0.1}],
        }

        from monitoring.collector import collect_snapshot

        result = collect_snapshot()

        self.assertEqual(result["cpu_percent"], 10.0)
        self.assertEqual(result["db_size_mb"], 150.5)
        self.assertEqual(result["db_connections"], 5)
        self.assertEqual(len(result["table_stats"]), 1)


class MonitoringEndpointsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("monitoradmin", "ma@test.com", "pass12345")
        cls.admin.is_staff = True
        cls.admin.save()
        cls.user = User.objects.create_user("regularuser", "ru@test.com", "pass12345")

    def setUp(self):
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)
        self.auth_client = APIClient()
        self.auth_client.force_authenticate(user=self.user)
        self.anon_client = APIClient()

    @patch("monitoring.collector.psutil")
    def test_current_returns_200_for_admin(self, mock_psutil):
        mock_psutil.cpu_percent.return_value = 10.0
        mem = MagicMock()
        mem.percent = 20.0
        mem.used = 1024 * 1024 * 1024
        mem.total = 4 * 1024 * 1024 * 1024
        mock_psutil.virtual_memory.return_value = mem
        disk = MagicMock()
        disk.percent = 30.0
        disk.used = 50 * 1024**3
        disk.total = 200 * 1024**3
        mock_psutil.disk_usage.return_value = disk

        r = self.admin_client.get("/api/admin/monitoring/current/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("cpu_percent", r.data)
        self.assertIn("db_size_mb", r.data)

    def test_current_forbidden_for_non_admin(self):
        r = self.auth_client.get("/api/admin/monitoring/current/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_current_unauthorized_for_anon(self):
        r = self.anon_client.get("/api/admin/monitoring/current/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_history_returns_200(self):
        r = self.admin_client.get("/api/admin/monitoring/history/?range=24h")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIsInstance(r.data, list)

    def test_history_7d_returns_200(self):
        r = self.admin_client.get("/api/admin/monitoring/history/?range=7d")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_table_stats_returns_200(self):
        r = self.admin_client.get("/api/admin/monitoring/table-stats/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIsInstance(r.data, list)
