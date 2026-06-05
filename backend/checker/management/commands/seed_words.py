from django.core.management.base import BaseCommand

from checker.models import Word, WordTopic
from checker.teeline import decompose_to_letters

TOPICS = [
    ("Common Words", "common"),
    ("Journalism", "journalism"),
    ("Business", "business"),
    ("Legal", "legal"),
]

WORDS = {
    "common": [
        "the", "be", "to", "of", "and", "in", "that", "have", "it", "for",
        "not", "on", "with", "he", "do", "at", "but", "we", "his", "from",
        "they", "she", "or", "an", "will", "my", "all", "would", "there",
        "their", "what", "so", "up", "out", "if", "about", "who", "get",
        "which", "go", "me", "when", "can", "no", "just", "him", "know",
        "take", "people", "into",
    ],
    "journalism": [
        "report", "source", "quote", "press", "editor", "publish", "article",
        "deadline", "interview", "breaking", "headline", "column", "feature",
        "broadcast", "journalist",
    ],
    "business": [
        "market", "profit", "invest", "budget", "contract", "manage",
        "strategy", "revenue", "client", "meeting", "project", "target",
        "growth", "finance", "company",
    ],
    "legal": [
        "court", "judge", "law", "trial", "evidence", "witness", "verdict",
        "appeal", "charge", "counsel", "defend", "guilty", "sentence",
        "statute", "justice",
    ],
}


def _difficulty(teeline_letters: str) -> str:
    length = len(teeline_letters)
    if length <= 3:
        return "beginner"
    elif length <= 5:
        return "intermediate"
    return "advanced"


class Command(BaseCommand):
    help = "Seed the database with common Teeline practice words"

    def handle(self, *args, **options):
        topic_objects = {}
        for name, slug in TOPICS:
            topic, _ = WordTopic.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )
            topic_objects[slug] = topic

        created_count = 0
        for topic_slug, words in WORDS.items():
            topic = topic_objects[topic_slug]
            for word_text in words:
                teeline = decompose_to_letters(word_text)
                difficulty = _difficulty(teeline)
                _, created = Word.objects.get_or_create(
                    text=word_text,
                    defaults={
                        "teeline_letters": teeline,
                        "difficulty": difficulty,
                        "topic": topic,
                        "is_curated": False,
                    },
                )
                if created:
                    created_count += 1

        total = sum(len(w) for w in WORDS.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_count} words ({total - created_count} already existed)"
            )
        )
