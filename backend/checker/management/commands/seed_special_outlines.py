"""Seed special outline mappings from teeline-online reference data."""
import json
import os
from django.core.management.base import BaseCommand
from checker.models import SpecialOutline, Symbol

SPECIAL_OUTLINES_JSON = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..",
    "data", "reference", "teeline-online",
    "website", "src", "lib", "data", "special-outlines.json",
)

class Command(BaseCommand):
    help = "Seed special outline word mappings from teeline-online reference data"

    def handle(self, *args, **options):
        json_path = os.path.normpath(SPECIAL_OUTLINES_JSON)
        if not os.path.isfile(json_path):
            self.stderr.write(f"Special outlines JSON not found: {json_path}")
            return

        with open(json_path, "r") as f:
            data = json.load(f)

        created = 0
        skipped = 0

        for entry in data:
            letter_grouping = entry["letterGrouping"].upper()

            try:
                symbol = Symbol.objects.get(letter=letter_grouping)
            except Symbol.DoesNotExist:
                symbol, _ = Symbol.objects.get_or_create(
                    letter=letter_grouping,
                    defaults={
                        "name": f"{letter_grouping} special",
                        "symbol_type": "grouping" if len(letter_grouping) > 1 else "letter",
                    },
                )

            for meaning in entry["meanings"]:
                _, was_created = SpecialOutline.objects.get_or_create(
                    symbol=symbol,
                    meaning=meaning.lower(),
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(f"Special outlines: {created} created, {skipped} skipped")
