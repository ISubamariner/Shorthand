import logging
import uuid

from django.db import IntegrityError

from accounts.models import AnonymousSession

logger = logging.getLogger(__name__)


class AnonymousSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.anonymous_session = None
        raw_token = request.META.get("HTTP_X_SESSION_TOKEN")
        if raw_token and not request.user.is_authenticated:
            try:
                token = uuid.UUID(raw_token)
            except ValueError:
                return self.get_response(request)
            try:
                session, created = AnonymousSession.objects.get_or_create(
                    session_token=token
                )
                if not created:
                    session.save(update_fields=["last_active"])
                request.anonymous_session = session
            except IntegrityError:
                session = AnonymousSession.objects.filter(session_token=token).first()
                if session:
                    session.save(update_fields=["last_active"])
                request.anonymous_session = session
            except Exception:
                logger.exception("Failed to load anonymous session")
        return self.get_response(request)
