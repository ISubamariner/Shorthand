from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from admin_api.permissions import IsAdminUser
from admin_api.serializers import AdminSymbolSerializer, AdminWordSerializer
from admin_api.services import log_audit
from checker.models import Symbol, Word


class SymbolListCreateView(ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminSymbolSerializer
    queryset = Symbol.objects.all()
    pagination_class = None

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(
            actor=self.request.user,
            action="content.symbol.create",
            target_type="symbol",
            target_id=instance.pk,
            details={"data": serializer.data},
        )


class SymbolDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminSymbolSerializer
    queryset = Symbol.objects.all()

    def perform_update(self, serializer):
        before = AdminSymbolSerializer(self.get_object()).data
        instance = serializer.save()
        log_audit(
            actor=self.request.user,
            action="content.symbol.update",
            target_type="symbol",
            target_id=instance.pk,
            details={"before": before, "after": serializer.data},
        )

    def perform_destroy(self, instance):
        data = AdminSymbolSerializer(instance).data
        pk = instance.pk
        instance.delete()
        log_audit(
            actor=self.request.user,
            action="content.symbol.delete",
            target_type="symbol",
            target_id=pk,
            details={"data": data},
        )


class WordListCreateView(ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminWordSerializer
    queryset = Word.objects.select_related("topic").all()
    pagination_class = None

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(
            actor=self.request.user,
            action="content.word.create",
            target_type="word",
            target_id=instance.pk,
            details={"data": serializer.data},
        )


class WordDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminWordSerializer
    queryset = Word.objects.select_related("topic").all()

    def perform_update(self, serializer):
        before = AdminWordSerializer(self.get_object()).data
        instance = serializer.save()
        log_audit(
            actor=self.request.user,
            action="content.word.update",
            target_type="word",
            target_id=instance.pk,
            details={"before": before, "after": serializer.data},
        )

    def perform_destroy(self, instance):
        data = AdminWordSerializer(instance).data
        pk = instance.pk
        instance.delete()
        log_audit(
            actor=self.request.user,
            action="content.word.delete",
            target_type="word",
            target_id=pk,
            details={"data": data},
        )
