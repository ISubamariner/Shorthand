from rest_framework.permissions import BasePermission


class AllowAnonymousSession(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            or getattr(request, "anonymous_session", None) is not None
        )
