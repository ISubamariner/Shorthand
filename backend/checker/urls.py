from django.urls import path

from .views import (
    AttemptDetailView,
    AttemptImageView,
    AttemptListView,
    LeaderboardView,
    ProgressView,
    SymbolDetailView,
    SymbolListView,
)
from .word_views import (
    WordDetailView,
    WordListView,
    WordProgressView,
    WordSessionCompleteView,
    WordSessionDetailView,
    WordSessionListView,
    WordTopicListView,
)

urlpatterns = [
    path("symbols/", SymbolListView.as_view(), name="symbol-list"),
    path("symbols/<str:letter>/", SymbolDetailView.as_view(), name="symbol-detail"),
    path("attempts/", AttemptListView.as_view(), name="attempt-list"),
    path("attempts/<uuid:pk>/", AttemptDetailView.as_view(), name="attempt-detail"),
    path("attempts/<uuid:pk>/image/", AttemptImageView.as_view(), name="attempt-image"),
    path("progress/", ProgressView.as_view(), name="progress"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("word-topics/", WordTopicListView.as_view(), name="word-topic-list"),
    path("words/", WordListView.as_view(), name="word-list"),
    path("words/<uuid:pk>/", WordDetailView.as_view(), name="word-detail"),
    path("word-sessions/", WordSessionListView.as_view(), name="word-session-list"),
    path("word-sessions/<uuid:pk>/", WordSessionDetailView.as_view(), name="word-session-detail"),
    path("word-sessions/<uuid:pk>/complete/", WordSessionCompleteView.as_view(), name="word-session-complete"),
    path("word-progress/", WordProgressView.as_view(), name="word-progress"),
]
