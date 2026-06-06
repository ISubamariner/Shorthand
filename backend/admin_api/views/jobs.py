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
