from django.test import TestCase
from checker.models import Symbol


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
