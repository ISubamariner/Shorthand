from django.urls import path

from .views import (
    AttemptDetailView,
    AttemptListView,
    ProgressView,
    SymbolDetailView,
    SymbolListView,
)

urlpatterns = [
    path("symbols/", SymbolListView.as_view(), name="symbol-list"),
    path("symbols/<str:letter>/", SymbolDetailView.as_view(), name="symbol-detail"),
    path("attempts/", AttemptListView.as_view(), name="attempt-list"),
    path("attempts/<uuid:pk>/", AttemptDetailView.as_view(), name="attempt-detail"),
    path("progress/", ProgressView.as_view(), name="progress"),
]
