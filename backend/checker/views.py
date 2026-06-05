import hashlib

from django.http import HttpResponse
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from .models import UserStats, WordAttemptSession
from .permissions import AllowAnonymousSession
from .repositories import AttemptRepository, SymbolRepository
from .serializers import (
    AttemptCreateSerializer,
    AttemptSerializer,
    LeaderboardEntrySerializer,
    ProgressResponseSerializer,
    SymbolSerializer,
)
from .services import get_progress, submit_attempt


class AttemptSubmitThrottle(SimpleRateThrottle):
    rate = "10/min"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return self.cache_format % {"scope": "attempt", "ident": request.user.pk}
        session = getattr(request, "anonymous_session", None)
        if session:
            return self.cache_format % {"scope": "attempt", "ident": str(session.session_token)}
        ident = self.get_ident(request)
        return self.cache_format % {"scope": "attempt", "ident": ident}


def _get_owner(request):
    if request.user.is_authenticated:
        return {"user": request.user, "session": None}
    return {"user": None, "session": getattr(request, "anonymous_session", None)}


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
    permission_classes = [AllowAnonymousSession]

    def get(self, request):
        attempts = AttemptRepository.get_by_owner(**_get_owner(request))
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

        word_session = None
        word_session_id = serializer.validated_data.get("word_session")
        if word_session_id:
            owner = _get_owner(request)
            owner_filter = {}
            if owner["user"]:
                owner_filter["user"] = owner["user"]
            else:
                owner_filter["anonymous_session"] = owner["session"]
            word_session = WordAttemptSession.objects.get(
                id=word_session_id, **owner_filter
            )

        attempt = submit_attempt(
            **_get_owner(request),
            symbol_letter=serializer.validated_data["symbol_letter"],
            image_data=serializer.validated_data["image_data"],
            word_session=word_session,
            word_position=serializer.validated_data.get("word_position"),
        )
        return Response(AttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class AttemptDetailView(APIView):
    permission_classes = [AllowAnonymousSession]

    def get(self, request, pk):
        attempt = AttemptRepository.get_by_id(pk, **_get_owner(request))
        return Response(AttemptSerializer(attempt).data)


class AttemptImageView(APIView):
    permission_classes = [AllowAnonymousSession]

    def get(self, request, pk):
        attempt = AttemptRepository.get_by_id(pk, **_get_owner(request))
        if not attempt.image_data:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return HttpResponse(
            bytes(attempt.image_data),
            content_type="image/png",
            headers={"Cache-Control": "private, max-age=86400"},
        )


class ProgressView(APIView):
    permission_classes = [AllowAnonymousSession]

    def get(self, request):
        progress = get_progress(**_get_owner(request))
        return Response(ProgressResponseSerializer(progress).data)


class LeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        entries = (
            UserStats.objects.select_related("user", "anonymous_session")
            .filter(total_score__gt=0)
            .order_by("-total_score")[:50]
        )

        owner = _get_owner(request)
        result = []
        for rank, stats in enumerate(entries, 1):
            if stats.user:
                display_name = stats.user.username
                is_current = owner["user"] == stats.user if owner["user"] else False
            else:
                token_hash = hashlib.sha256(str(stats.anonymous_session.session_token).encode()).hexdigest()[:8]
                display_name = f"Anonymous-{token_hash}"
                is_current = (
                    owner["session"] == stats.anonymous_session
                    if owner["session"]
                    else False
                )
            result.append(
                {
                    "rank": rank,
                    "display_name": display_name,
                    "total_score": stats.total_score,
                    "best_streak": stats.best_streak,
                    "is_current_user": is_current,
                }
            )

        return Response(LeaderboardEntrySerializer(result, many=True).data)
