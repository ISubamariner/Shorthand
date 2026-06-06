import sys

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Grant admin (is_staff) access to a user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(f'User "{username}" not found.')
            return

        user.is_staff = True
        user.save(update_fields=["is_staff"])
        self.stdout.write(f'User "{username}" is now an admin.')
