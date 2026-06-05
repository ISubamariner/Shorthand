from django.contrib.auth.models import User
from django.db.models import Count, Q, QuerySet

from accounts.models import AnonymousSession

from .models import Attempt, Symbol


class SymbolRepository:
    @staticmethod
    def get_all() -> QuerySet[Symbol]:
        return Symbol.objects.all()

    @staticmethod
    def get_by_letter(letter: str) -> Symbol:
        return Symbol.objects.get(letter=letter.upper())


class AttemptRepository:
    @staticmethod
    def _owner_filter(user: User | None = None, session: AnonymousSession | None = None) -> Q:
        """Helper to build Q filter for owner (user or session)."""
        if user and session:
            raise ValueError("Cannot specify both user and session")
        if user:
            return Q(user=user)
        if session:
            return Q(anonymous_session=session)
        raise ValueError("Either user or session must be provided")

    @staticmethod
    def create(
        symbol: Symbol,
        user: User | None = None,
        session: AnonymousSession | None = None,
        image_data: bytes = b"",
        word_session=None,
        word_position: int | None = None,
    ) -> Attempt:
        return Attempt.objects.create(
            user=user,
            anonymous_session=session,
            symbol=symbol,
            image_data=image_data,
            word_session=word_session,
            word_position=word_position,
        )

    @staticmethod
    def get_by_id(
        attempt_id,
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> Attempt:
        owner_filter = AttemptRepository._owner_filter(user, session)
        return Attempt.objects.get(Q(id=attempt_id) & owner_filter)

    @staticmethod
    def get_by_owner(
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> QuerySet[Attempt]:
        owner_filter = AttemptRepository._owner_filter(user, session)
        return Attempt.objects.filter(owner_filter)

    @staticmethod
    def get_progress(
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> list[dict]:
        owner_filter = AttemptRepository._owner_filter(user, session)
        return list(
            Attempt.objects.filter(owner_filter, status="completed")
            .values("symbol__letter")
            .annotate(
                total=Count("id"),
                correct=Count("id", filter=Q(is_correct=True)),
            )
            .order_by("symbol__letter")
        )

    @staticmethod
    def get_current_streak(
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> int:
        owner_filter = AttemptRepository._owner_filter(user, session)
        attempts = Attempt.objects.filter(
            owner_filter, status="completed"
        ).order_by("-created_at").values_list("is_correct", flat=True)

        streak = 0
        for is_correct in attempts:
            if is_correct:
                streak += 1
            else:
                break
        return streak

    @staticmethod
    def transfer_session_to_user(session: AnonymousSession, user: User) -> int:
        """Transfer all attempts from session to user. Returns count of attempts transferred."""
        count = Attempt.objects.filter(anonymous_session=session).update(
            user=user,
            anonymous_session=None,
        )
        return count
