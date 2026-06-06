from rest_framework.generics import ListAPIView

from admin_api.models import AuditLog
from admin_api.permissions import IsAdminUser
from admin_api.serializers import AuditLogSerializer


class AuditLogListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("actor").all()

    def get_queryset(self):
        qs = super().get_queryset()
        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)
        actor = self.request.query_params.get("actor")
        if actor:
            qs = qs.filter(actor__username=actor)
        target_type = self.request.query_params.get("target_type")
        if target_type:
            qs = qs.filter(target_type=target_type)
        return qs
