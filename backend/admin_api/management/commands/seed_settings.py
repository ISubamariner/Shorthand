from django.core.management.base import BaseCommand

from admin_api.models import SystemSetting

DEFAULTS = [
    (
        "practice_no_repeat_count",
        {
            "all": 10,
            "letter": 10,
            "grouping": 10,
        },
    ),
]


class Command(BaseCommand):
    help = "Seed default system settings (skips existing keys)"

    def handle(self, *args, **options):
        created_count = 0
        for key, value in DEFAULTS:
            _, created = SystemSetting.objects.get_or_create(
                key=key,
                defaults={"value": value},
            )
            if created:
                created_count += 1

        total = len(DEFAULTS)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_count} settings ({total - created_count} already existed)"
            )
        )
