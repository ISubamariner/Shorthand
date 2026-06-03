from django.contrib.auth.models import User
from django.db.models import Count, Q, QuerySet

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
    def create(user: User, symbol: Symbol, image_url: str) -> Attempt:
        return Attempt.objects.create(
            user=user,
            symbol=symbol,
            image_url=image_url,
        )

    @staticmethod
    def get_by_id(attempt_id, user: User) -> Attempt:
        return Attempt.objects.get(id=attempt_id, user=user)

    @staticmethod
    def get_by_user(user: User) -> QuerySet[Attempt]:
        return Attempt.objects.for_user(user)

    @staticmethod
    def get_user_progress(user: User) -> list[dict]:
        return list(
            Attempt.objects.filter(user=user, status="completed")
            .values("symbol__letter")
            .annotate(
                total=Count("id"),
                correct=Count("id", filter=Q(is_correct=True)),
            )
            .order_by("symbol__letter")
        )
