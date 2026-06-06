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
