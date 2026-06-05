import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import AnonymousSession
from checker.services import claim_anonymous_session

from .serializers import RegisterSerializer, UserSerializer
from .services import create_user

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_user(**serializer.validated_data)

        session_token = request.META.get("HTTP_X_SESSION_TOKEN")
        transferred = 0
        if session_token:
            try:
                transferred = claim_anonymous_session(session_token, user)
            except (AnonymousSession.DoesNotExist, ValueError):
                pass
            except Exception:
                logger.exception("Failed to transfer anonymous session to user %s", user.pk)

        data = UserSerializer(user).data
        data["transferred_attempts"] = transferred
        return Response(data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ClaimSessionView(APIView):
    def post(self, request):
        session_token = request.META.get("HTTP_X_SESSION_TOKEN")
        if not session_token:
            return Response(
                {"detail": "No session token provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            count = claim_anonymous_session(session_token, request.user)
        except (AnonymousSession.DoesNotExist, ValueError):
            return Response(
                {"detail": "Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"transferred_attempts": count})


class LogoutView(APIView):
    def post(self, request):
        from checker.models import Attempt

        Attempt.objects.filter(
            user=request.user, status=Attempt.Status.COMPLETED
        ).exclude(image_data=b"").update(image_data=b"")
        return Response(status=status.HTTP_204_NO_CONTENT)
