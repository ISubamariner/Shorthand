from django.contrib.auth.models import User
from django.db.models import Count, F, Q, QuerySet

from accounts.models import AnonymousSession

from .models import Word, WordAttemptSession, WordTopic


class WordTopicRepository:
    @staticmethod
    def get_all() -> QuerySet[WordTopic]:
        return WordTopic.objects.all()


class WordRepository:
    @staticmethod
    def get_all(
        difficulty: str | None = None,
        topic_slug: str | None = None,
    ) -> QuerySet[Word]:
        qs = Word.objects.select_related("topic")
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if topic_slug:
            qs = qs.filter(topic__slug=topic_slug)
        return qs

    @staticmethod
    def get_by_id(word_id) -> Word:
        return Word.objects.select_related("topic").get(id=word_id)


class WordSessionRepository:
    @staticmethod
    def _owner_filter(
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> Q:
        if user:
            return Q(user=user)
        elif session:
            return Q(anonymous_session=session)
        raise ValueError("Either user or session must be provided")

    @staticmethod
    def create(
        word: Word,
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> WordAttemptSession:
        return WordAttemptSession.objects.create(
            word=word,
            user=user,
            anonymous_session=session,
            letters_total=len(word.teeline_letters),
        )

    @staticmethod
    def get_by_id(
        session_id,
        user: User | None = None,
        session: AnonymousSession | None = None,
    ) -> WordAttemptSession:
        owner_filter = WordSessionRepository._owner_filter(user, session)
        return WordAttemptSession.objects.select_related("word", "word__topic").get(
            Q(id=session_id) & owner_filter
        )

    @staticmethod
    def get_progress(
        user: User | None = None,
        session: AnonymousSession | None = None,
        difficulty: str | None = None,
        topic_slug: str | None = None,
    ) -> list[dict]:
        owner_filter = WordSessionRepository._owner_filter(user, session)
        qs = WordAttemptSession.objects.filter(
            owner_filter,
            status=WordAttemptSession.Status.COMPLETED,
        )
        if difficulty:
            qs = qs.filter(word__difficulty=difficulty)
        if topic_slug:
            qs = qs.filter(word__topic__slug=topic_slug)

        return list(
            qs.values("word__id", "word__text")
            .annotate(
                total_sessions=Count("id"),
                perfect_sessions=Count(
                    "id",
                    filter=Q(letters_correct=F("letters_total")),
                ),
            )
            .order_by("word__text")
        )

    @staticmethod
    def transfer_session_to_user(
        anon_session: AnonymousSession,
        user: User,
    ) -> int:
        count = WordAttemptSession.objects.filter(
            anonymous_session=anon_session
        ).update(user=user, anonymous_session=None)
        return count
