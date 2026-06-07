"""Seed multi-letter grouping symbols."""
from django.core.management.base import BaseCommand
from checker.models import Symbol

GROUPINGS = [
    "ABT", "ANY", "AS", "BD", "BT", "CD", "CHF", "CM", "CR", "CV",
    "DB", "DR", "FB", "FL", "FM", "FR", "FW", "HV", "IF", "IS",
    "IT", "MB", "MN", "MNY", "MR", "NO", "NV", "NW", "O", "OM",
    "ON", "OTHR", "PV", "RF", "SD", "SE", "SHE", "SM", "SN", "SO",
    "TB", "THS", "TLN", "TR/THR", "US", "VN", "WF", "WN", "WR", "WRD",
    "WS",
]


class Command(BaseCommand):
    help = "Seed Teeline letter grouping symbols"

    def handle(self, *args, **options):
        created = 0
        for letter in GROUPINGS:
            _, was_created = Symbol.objects.update_or_create(
                letter=letter,
                defaults={"name": f"{letter} grouping", "symbol_type": "grouping"},
            )
            if was_created:
                created += 1

        total = Symbol.objects.filter(symbol_type="grouping").count()
        self.stdout.write(self.style.SUCCESS(
            f"Groupings: {created} created, {total} total"
        ))
