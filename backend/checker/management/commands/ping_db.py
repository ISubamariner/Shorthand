from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Run a lightweight query to keep the database connection alive and prevent Supabase auto-pause."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        self.stdout.write(self.style.SUCCESS("Database ping successful."))
