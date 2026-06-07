"""Seed multi-letter grouping symbols from teeline-online SVG reference files."""
import os
from django.core.management.base import BaseCommand
from checker.models import Symbol

GROUPINGS_SVG_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..",
    "data", "reference", "teeline-online", "outline-svgs", "letter-groupings",
)


class Command(BaseCommand):
    help = "Seed Teeline letter grouping symbols from reference SVGs"

    def handle(self, *args, **options):
        svg_dir = os.path.normpath(GROUPINGS_SVG_DIR)
        if not os.path.isdir(svg_dir):
            self.stderr.write(f"SVG directory not found: {svg_dir}")
            return

        svg_files = sorted(f for f in os.listdir(svg_dir) if f.endswith(".svg"))
        created = 0

        for svg_file in svg_files:
            stem = os.path.splitext(svg_file)[0]
            letter = stem.upper().replace(",", "/")
            name = f"{letter} grouping"

            _, was_created = Symbol.objects.update_or_create(
                letter=letter,
                defaults={"name": name, "symbol_type": "grouping"},
            )
            if was_created:
                created += 1

        total = Symbol.objects.filter(symbol_type="grouping").count()
        self.stdout.write(f"Groupings: {created} created, {total} total")
