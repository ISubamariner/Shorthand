from django.core.management.base import BaseCommand

from checker.models import Symbol

TEELINE_SYMBOLS = [
    ("A", "Alpha"), ("B", "Bravo"), ("C", "Charlie"), ("D", "Delta"),
    ("E", "Echo"), ("F", "Foxtrot"), ("G", "Golf"), ("H", "Hotel"),
    ("I", "India"), ("J", "Juliet"), ("K", "Kilo"), ("L", "Lima"),
    ("M", "Mike"), ("N", "November"), ("O", "Oscar"), ("P", "Papa"),
    ("Q", "Quebec"), ("R", "Romeo"), ("S", "Sierra"), ("T", "Tango"),
    ("U", "Uniform"), ("V", "Victor"), ("W", "Whiskey"), ("X", "X-ray"),
    ("Y", "Yankee"), ("Z", "Zulu"),
]


class Command(BaseCommand):
    help = "Seed the database with 26 Teeline letter symbols"

    def handle(self, *args, **options):
        created_count = 0
        for letter, name in TEELINE_SYMBOLS:
            _, created = Symbol.objects.get_or_create(
                letter=letter,
                defaults={"name": name},
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} symbols ({26 - created_count} already existed)"))
