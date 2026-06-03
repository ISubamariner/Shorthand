import uuid

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Attempt, Symbol


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
