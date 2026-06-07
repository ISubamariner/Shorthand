from datetime import timedelta

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminUser
from monitoring.collector import collect_snapshot
from monitoring.models import SystemSnapshot


class MonitoringCurrentView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = collect_snapshot()
        return Response(data)


class MonitoringHistoryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        range_param = request.query_params.get("range", "24h")
        if range_param == "7d":
            cutoff = timezone.now() - timedelta(days=7)
        else:
            cutoff = timezone.now() - timedelta(hours=24)

        snapshots = SystemSnapshot.objects.filter(
            timestamp__gte=cutoff
        ).order_by("timestamp")

        if range_param == "7d":
            snapshot_list = list(snapshots)
            snapshots_sampled = snapshot_list[::6]
        else:
            snapshots_sampled = list(snapshots)

        data = [
            {
                "timestamp": s.timestamp.isoformat(),
                "cpu_percent": s.cpu_percent,
                "memory_percent": s.memory_percent,
                "disk_percent": s.disk_percent,
                "db_size_mb": s.db_size_mb,
                "db_connections": s.db_connections,
            }
            for s in snapshots_sampled
        ]
        return Response(data)


class MonitoringTableStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        latest = SystemSnapshot.objects.first()
        if latest:
            return Response(latest.table_stats)
        data = collect_snapshot()
        return Response(data.get("table_stats", []))
