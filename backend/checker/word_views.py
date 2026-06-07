from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from config.exceptions import AppError

from .models import WordAttemptSession
from .permissions import AllowAnonymousSession
from .word_repository import WordRepository, WordTopicRepository
from .word_recognition_service import (
    suggest_words_by_prefix,
    suggest_words_by_skeleton,
)
from .word_serializers import (
    WordListSerializer,
    WordProgressSerializer,
    WordSerializer,
    WordSessionCreateSerializer,
    WordSessionSerializer,
    WordSuggestionSerializer,
    WordTopicSerializer,
)
from .word_service import (
    complete_session,
    get_session_detail,
    get_word_progress,
    start_session,
)


def _get_owner(request):
    if request.user.is_authenticated:
        return {"user": request.user, "session": None}
    return {"user": None, "session": getattr(request, "anonymous_session", None)}


class WordTopicListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        topics = WordTopicRepository.get_all()
        return Response(WordTopicSerializer(topics, many=True).data)


class WordListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        difficulty = request.query_params.get("difficulty")
        topic = request.query_params.get("topic")
        words = WordRepository.get_all(difficulty=difficulty, topic_slug=topic)
        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"
        paginator.max_page_size = 1000
        page = paginator.paginate_queryset(words, request)
        return paginator.get_paginated_response(WordListSerializer(page, many=True).data)


class WordDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        word = WordRepository.get_by_id(pk)
        return Response(WordSerializer(word).data)


class WordSessionListView(APIView):
    permission_classes = [AllowAnonymousSession]

    def post(self, request):
        serializer = WordSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        word_session = start_session(
            word_id=serializer.validated_data["word_id"],
            **_get_owner(request),
        )
        detail = get_session_detail(word_session.id, **_get_owner(request))
        return Response(
            WordSessionSerializer(
                detail["session"],
                context={"letter_results": detail["letter_results"]},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class WordSessionDetailView(APIView):
    permission_classes = [AllowAnonymousSession]

    def get(self, request, pk):
        detail = get_session_detail(pk, **_get_owner(request))
        data = WordSessionSerializer(detail["session"]).data
        data["letter_results"] = detail["letter_results"]
        return Response(data)


class WordSessionCompleteView(APIView):
    permission_classes = [AllowAnonymousSession]

    def post(self, request, pk):
        word_session = complete_session(pk, **_get_owner(request))
        detail = get_session_detail(pk, **_get_owner(request))
        data = WordSessionSerializer(detail["session"]).data
        data["letter_results"] = detail["letter_results"]
        return Response(data)


class WordProgressView(APIView):
    permission_classes = [AllowAnonymousSession]

    def get(self, request):
        difficulty = request.query_params.get("difficulty")
        topic = request.query_params.get("topic")
        progress = get_word_progress(
            **_get_owner(request),
            difficulty=difficulty,
            topic_slug=topic,
        )
        return Response(WordProgressSerializer(progress, many=True).data)


class WordSuggestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def get(self, request):
        skeleton = request.query_params.get("skeleton", "").strip()[:100]
        prefix = request.query_params.get("prefix", "").strip()[:100]

        if skeleton:
            suggestions = suggest_words_by_skeleton(skeleton.upper())
        elif prefix:
            suggestions = suggest_words_by_prefix(prefix.upper())
        else:
            raise AppError("Provide 'skeleton' or 'prefix' query parameter")

        return Response(WordSuggestionSerializer(suggestions, many=True).data)
