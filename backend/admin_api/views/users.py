from django.contrib.auth.models import User
from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView

from admin_api.permissions import IsAdminUser
from admin_api.serializers import AdminUserListSerializer, AdminUserDetailSerializer
from admin_api.services import log_audit


class UserListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserListSerializer
    queryset = User.objects.all().order_by("-date_joined")
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email"]


class UserDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserDetailSerializer
    queryset = User.objects.all()

    def perform_update(self, serializer):
        before = {f: getattr(self.get_object(), f) for f in serializer.validated_data}
        instance = serializer.save()
        after = {f: getattr(instance, f) for f in serializer.validated_data}
        log_audit(
            actor=self.request.user,
            action="user.update",
            target_type="user",
            target_id=instance.pk,
            details={"before": before, "after": after},
        )
