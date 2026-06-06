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
