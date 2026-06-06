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

    def patch(self, request):
        user = request.user
        email = request.data.get("email")
        new_password = request.data.get("new_password")
        current_password = request.data.get("current_password")

        if new_password:
            if not current_password or not user.check_password(current_password):
                return Response(
                    {"fields": {"current_password": "Current password is incorrect."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if len(new_password) < 8:
                return Response(
                    {"fields": {"new_password": "Password must be at least 8 characters."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(new_password)

        if email is not None:
            user.email = email

        user.save()
        return Response(UserSerializer(user).data)


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
