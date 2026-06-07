import logging
import sys

import psutil
from django.db import connection

logger = logging.getLogger(__name__)

_PROCESS_CREATE_TIME = psutil.Process().create_time()
_DISK_PATH = "/" if sys.platform != "win32" else "C:\\"


def collect_server_metrics():
    cpu = psutil.cpu_percent(interval=0)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(_DISK_PATH)
    import time

    return {
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_used_mb": round(mem.used / (1024 * 1024), 1),
        "memory_total_mb": round(mem.total / (1024 * 1024), 1),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / (1024**3), 1),
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "process_uptime_seconds": round(time.time() - _PROCESS_CREATE_TIME, 1),
    }


def collect_db_metrics():
    if connection.vendor != "postgresql":
        return {"db_size_mb": 0, "db_connections": 0, "table_stats": []}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_database_size(current_database())")
            row = cursor.fetchone()
            db_size_bytes = row[0] if row else 0

            cursor.execute(
                "SELECT count(*) FROM pg_stat_activity "
                "WHERE datname = current_database()"
            )
            row = cursor.fetchone()
            db_connections = row[0] if row else 0

            cursor.execute("""
                WITH sizes AS (
                    SELECT
                        c.relname AS name,
                        COALESCE(s.n_live_tup, 0) AS row_count,
                        pg_total_relation_size(c.oid) AS size_bytes
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
                    WHERE n.nspname = 'public'
                      AND c.relkind = 'r'
                )
                SELECT name, row_count, size_bytes FROM sizes ORDER BY size_bytes DESC
            """)
            table_stats = [
                {
                    "name": row[0],
                    "row_count": row[1],
                    "size_mb": round(row[2] / (1024 * 1024), 3),
                }
                for row in cursor.fetchall()
            ]

        return {
            "db_size_mb": round(db_size_bytes / (1024 * 1024), 2),
            "db_connections": db_connections,
            "table_stats": table_stats,
        }
    except Exception:
        logger.exception("Failed to collect DB metrics")
        return {"db_size_mb": 0, "db_connections": 0, "table_stats": []}


def collect_snapshot():
    data = collect_server_metrics()
    data.update(collect_db_metrics())
    return data
