# Uses Django's built-in User model — no custom model needed.

import uuid
from django.db import models


class AnonymousSession(models.Model):
    session_token = models.UUIDField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {str(self.session_token)[:8]}"
