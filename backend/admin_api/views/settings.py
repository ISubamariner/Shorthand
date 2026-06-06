from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.models import SystemSetting
from admin_api.permissions import IsAdminUser
from admin_api.serializers import SystemSettingSerializer
from admin_api.services import log_audit


class SystemSettingsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        settings = SystemSetting.objects.all()
        return Response(SystemSettingSerializer(settings, many=True).data)

    @transaction.atomic
    def patch(self, request):
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Expected a list of settings."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = []
        for item in request.data:
            key = item.get("key")
            value = item.get("value")
            if not key or value is None:
                continue
            try:
                setting = SystemSetting.objects.select_for_update().get(key=key)
                before = setting.value
                setting.value = value
                setting.updated_by = request.user
                setting.save()
                log_audit(
                    actor=request.user,
                    action="settings.update",
                    target_type="setting",
                    target_id=key,
                    details={"before": before, "after": value},
                )
                updated.append(setting)
            except SystemSetting.DoesNotExist:
                continue
        return Response(SystemSettingSerializer(updated, many=True).data)
