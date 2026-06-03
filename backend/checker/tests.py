import uuid

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Attempt, Symbol
from .repositories import AttemptRepository, SymbolRepository


class SymbolModelTest(TestCase):
    def test_create_symbol(self):
        symbol = Symbol.objects.create(
            letter="A",
            name="Alpha",
            reference_image_url="https://example.com/a.png",
        )
        self.assertEqual(str(symbol), "A — Alpha")
        self.assertEqual(symbol.letter, "A")

    def test_letter_is_unique(self):
        Symbol.objects.create(letter="A", name="Alpha")
        with self.assertRaises(Exception):
            Symbol.objects.create(letter="A", name="Alpha duplicate")


class AttemptModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.symbol = Symbol.objects.create(letter="A", name="Alpha")

    def test_create_attempt_defaults_to_pending(self):
        attempt = Attempt.objects.create(
            user=self.user,
            symbol=self.symbol,
            image_url="https://example.com/drawing.png",
        )
        self.assertEqual(attempt.status, "pending")
        self.assertIsInstance(attempt.id, uuid.UUID)
        self.assertIsNone(attempt.predicted_label)
        self.assertIsNone(attempt.confidence)
        self.assertIsNone(attempt.is_correct)

    def test_user_scoped_manager(self):
        Attempt.objects.create(user=self.user, symbol=self.symbol, image_url="https://ex.com/1.png")
        other_user = User.objects.create_user("other", password="testpass123")
        Attempt.objects.create(user=other_user, symbol=self.symbol, image_url="https://ex.com/2.png")
        self.assertEqual(Attempt.objects.for_user(self.user).count(), 1)

    def test_has_updated_at(self):
        attempt = Attempt.objects.create(
            user=self.user, symbol=self.symbol, image_url="https://ex.com/1.png"
        )
        self.assertIsNotNone(attempt.updated_at)


class SymbolRepositoryTest(TestCase):
    def setUp(self):
        Symbol.objects.create(letter="A", name="Alpha")
        Symbol.objects.create(letter="B", name="Bravo")

    def test_get_all_returns_all_symbols(self):
        symbols = SymbolRepository.get_all()
        self.assertEqual(len(symbols), 2)

    def test_get_by_letter(self):
        symbol = SymbolRepository.get_by_letter("A")
        self.assertEqual(symbol.name, "Alpha")

    def test_get_by_letter_not_found(self):
        with self.assertRaises(Symbol.DoesNotExist):
            SymbolRepository.get_by_letter("Z")


class AttemptRepositoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123")
        self.symbol_a = Symbol.objects.create(letter="A", name="Alpha")
        self.symbol_b = Symbol.objects.create(letter="B", name="Bravo")

    def test_create_attempt(self):
        attempt = AttemptRepository.create(
            user=self.user,
            symbol=self.symbol_a,
            image_url="https://example.com/drawing.png",
        )
        self.assertEqual(attempt.status, "pending")
        self.assertEqual(attempt.symbol.letter, "A")

    def test_get_by_user(self):
        AttemptRepository.create(user=self.user, symbol=self.symbol_a, image_url="https://ex.com/1.png")
        AttemptRepository.create(user=self.user, symbol=self.symbol_b, image_url="https://ex.com/2.png")
        attempts = AttemptRepository.get_by_user(self.user)
        self.assertEqual(len(attempts), 2)

    def test_get_user_progress(self):
        a1 = AttemptRepository.create(user=self.user, symbol=self.symbol_a, image_url="https://ex.com/1.png")
        a1.is_correct = True
        a1.status = "completed"
        a1.save()
        a2 = AttemptRepository.create(user=self.user, symbol=self.symbol_a, image_url="https://ex.com/2.png")
        a2.is_correct = False
        a2.status = "completed"
        a2.save()

        progress = AttemptRepository.get_user_progress(self.user)
        entry = next(p for p in progress if p["symbol__letter"] == "A")
        self.assertEqual(entry["total"], 2)
        self.assertEqual(entry["correct"], 1)
