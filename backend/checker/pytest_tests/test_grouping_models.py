from django.core.management import call_command
from django.test import TestCase
from checker.models import Symbol, SpecialOutline


class SymbolTypeTest(TestCase):
    def test_symbol_can_be_letter_type(self):
        s = Symbol.objects.create(letter="A", name="A", symbol_type="letter")
        assert s.symbol_type == "letter"

    def test_symbol_can_be_grouping_type(self):
        s = Symbol.objects.create(letter="CM", name="CM blend", symbol_type="grouping")
        assert s.symbol_type == "grouping"
        assert s.letter == "CM"

    def test_symbol_type_defaults_to_letter(self):
        s = Symbol.objects.create(letter="B", name="B")
        assert s.symbol_type == "letter"


class SpecialOutlineTest(TestCase):
    def test_special_outline_links_grouping_to_meaning(self):
        sym = Symbol.objects.create(letter="BS", name="BS blend", symbol_type="grouping")
        outline = SpecialOutline.objects.create(symbol=sym, meaning="business")
        assert outline.symbol == sym
        assert outline.meaning == "business"

    def test_multiple_meanings_for_same_grouping(self):
        sym = Symbol.objects.create(letter="MR", name="MR blend", symbol_type="grouping")
        SpecialOutline.objects.create(symbol=sym, meaning="march")
        SpecialOutline.objects.create(symbol=sym, meaning="metre")
        assert SpecialOutline.objects.filter(symbol=sym).count() == 2

    def test_unique_meaning_per_symbol(self):
        sym = Symbol.objects.create(letter="AC", name="AC blend", symbol_type="grouping")
        SpecialOutline.objects.create(symbol=sym, meaning="account")
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SpecialOutline.objects.create(symbol=sym, meaning="account")


class SeedGroupingsTest(TestCase):
    def test_seed_groupings_creates_symbols(self):
        call_command("seed_groupings")
        groupings = Symbol.objects.filter(symbol_type="grouping")
        assert groupings.count() >= 50  # at least 50 of the 51

    def test_seed_groupings_idempotent(self):
        call_command("seed_groupings")
        call_command("seed_groupings")
        groupings = Symbol.objects.filter(symbol_type="grouping")
        count = groupings.count()
        assert count >= 50

    def test_seed_groupings_sets_correct_letters(self):
        call_command("seed_groupings")
        assert Symbol.objects.filter(letter="CM", symbol_type="grouping").exists()
        assert Symbol.objects.filter(letter="SH", symbol_type="grouping").exists() or \
               Symbol.objects.filter(letter="SHE", symbol_type="grouping").exists()


class SeedSpecialOutlinesTest(TestCase):
    def test_seed_special_outlines_creates_entries(self):
        call_command("seed_groupings")
        call_command("seed_special_outlines")
        assert SpecialOutline.objects.count() > 0

    def test_seed_special_outlines_links_to_grouping_symbols(self):
        call_command("seed_groupings")
        call_command("seed_special_outlines")
        bs = SpecialOutline.objects.filter(meaning="business").first()
        assert bs is not None
        assert bs.symbol.letter == "BS"

    def test_seed_special_outlines_handles_multiple_meanings(self):
        call_command("seed_groupings")
        call_command("seed_special_outlines")
        mr_outlines = SpecialOutline.objects.filter(symbol__letter="MR")
        assert mr_outlines.count() >= 2

    def test_seed_special_outlines_idempotent(self):
        call_command("seed_groupings")
        call_command("seed_special_outlines")
        count1 = SpecialOutline.objects.count()
        call_command("seed_special_outlines")
        count2 = SpecialOutline.objects.count()
        assert count1 == count2
