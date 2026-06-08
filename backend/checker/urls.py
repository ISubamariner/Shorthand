from django.urls import path

from .views import (
    AttemptDetailView,
    AttemptImageView,
    AttemptListView,
    LeaderboardView,
    PracticeSettingsView,
    ProgressView,
    SpecialOutlineListView,
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
    WordSuggestView,
    WordTopicListView,
)

urlpatterns = [
    path("symbols/", SymbolListView.as_view(), name="symbol-list"),
    path("symbols/<str:letter>/", SymbolDetailView.as_view(), name="symbol-detail"),
    path("special-outlines/", SpecialOutlineListView.as_view(), name="special-outline-list"),
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
    path("word-suggest/", WordSuggestView.as_view(), name="word-suggest"),
    path("practice-settings/", PracticeSettingsView.as_view(), name="practice-settings"),
]
