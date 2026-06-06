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

    def patch(self, request):
        updated = []
        for item in request.data:
            key = item.get("key")
            value = item.get("value")
            try:
                setting = SystemSetting.objects.get(key=key)
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
