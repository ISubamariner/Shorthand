from django.http import HttpResponse
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class AttemptSubmitThrottle(UserRateThrottle):
    rate = "10/min"

from .repositories import AttemptRepository, SymbolRepository
from .serializers import (
    AttemptCreateSerializer,
    AttemptSerializer,
    ProgressResponseSerializer,
    ProgressSerializer,
    SymbolSerializer,
)
from .services import get_user_progress, submit_attempt


class SymbolListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        symbols = SymbolRepository.get_all()
        return Response(SymbolSerializer(symbols, many=True).data)


class SymbolDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, letter):
        symbol = SymbolRepository.get_by_letter(letter)
        return Response(SymbolSerializer(symbol).data)


class AttemptListView(APIView):
    def get(self, request):
        attempts = AttemptRepository.get_by_user(request.user)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(attempts, request)
        return paginator.get_paginated_response(AttemptSerializer(page, many=True).data)

    def get_throttles(self):
        if self.request.method == "POST":
            return [AttemptSubmitThrottle()]
        return []

    def post(self, request):
        serializer = AttemptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = submit_attempt(
            user=request.user,
            symbol_letter=serializer.validated_data["symbol_letter"],
            image_data=serializer.validated_data["image_data"],
        )
        return Response(AttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class AttemptDetailView(APIView):
    def get(self, request, pk):
        attempt = AttemptRepository.get_by_id(pk, request.user)
        return Response(AttemptSerializer(attempt).data)


class AttemptImageView(APIView):
    def get(self, request, pk):
        attempt = AttemptRepository.get_by_id(pk, request.user)
        if not attempt.image_data:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return HttpResponse(
            bytes(attempt.image_data),
            content_type="image/png",
            headers={"Cache-Control": "private, max-age=86400"},
        )


class ProgressView(APIView):
    def get(self, request):
        progress = get_user_progress(request.user)
        return Response(ProgressResponseSerializer(progress).data)
