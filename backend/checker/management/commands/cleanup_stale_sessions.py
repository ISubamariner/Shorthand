from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import AnonymousSession
from checker.models import Attempt


class Command(BaseCommand):
    help = "Delete anonymous sessions inactive for >24h and clear their leftover image data"

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=24)
        stale = AnonymousSession.objects.filter(last_active__lt=cutoff)

        img_cleared = Attempt.objects.filter(
            anonymous_session__in=stale
        ).exclude(image_data=b"").update(image_data=b"")

        count = stale.count()
        stale.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {count} stale sessions, cleared {img_cleared} images"
            )
        )
