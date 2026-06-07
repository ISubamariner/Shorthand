from unittest.mock import MagicMock, patch

from django.test import TestCase


class CollectorServerMetricsTest(TestCase):

    @patch("monitoring.collector.time")
    @patch("monitoring.collector.psutil")
    def test_collect_server_metrics_returns_expected_keys(self, mock_psutil, mock_time):
        mock_psutil.cpu_percent.return_value = 42.5
        mem = MagicMock()
        mem.percent = 65.0
        mem.used = 4 * 1024 * 1024 * 1024  # 4 GB in bytes
        mem.total = 16 * 1024 * 1024 * 1024
        mock_psutil.virtual_memory.return_value = mem
        disk = MagicMock()
        disk.percent = 55.0
        disk.used = 100 * 1024 * 1024 * 1024
        disk.total = 500 * 1024 * 1024 * 1024
        mock_psutil.disk_usage.return_value = disk

        # Mock time to return consistent uptime
        import monitoring.collector
        mock_time.time.return_value = monitoring.collector._START_TIME + 3600.5

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
        self.assertAlmostEqual(result["process_uptime_seconds"], 3600.5)


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
