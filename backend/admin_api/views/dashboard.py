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
