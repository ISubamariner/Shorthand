import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status as http_status

from .models import Attempt, Symbol
from .repositories import AttemptRepository, SymbolRepository
from .services import submit_attempt, get_user_progress


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
        )
        self.assertEqual(attempt.status, "pending")
        self.assertIsInstance(attempt.id, uuid.UUID)
        self.assertIsNone(attempt.predicted_label)
        self.assertIsNone(attempt.confidence)
        self.assertIsNone(attempt.is_correct)

    def test_user_scoped_manager(self):
        Attempt.objects.create(user=self.user, symbol=self.symbol)
        other_user = User.objects.create_user("other", password="testpass123")
        Attempt.objects.create(user=other_user, symbol=self.symbol)
        self.assertEqual(Attempt.objects.for_user(self.user).count(), 1)

    def test_has_updated_at(self):
        attempt = Attempt.objects.create(user=self.user, symbol=self.symbol)
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
        )
        self.assertEqual(attempt.status, "pending")
        self.assertEqual(attempt.symbol.letter, "A")

    def test_get_by_user(self):
        AttemptRepository.create(user=self.user, symbol=self.symbol_a)
        AttemptRepository.create(user=self.user, symbol=self.symbol_b)
        attempts = AttemptRepository.get_by_user(self.user)
        self.assertEqual(len(attempts), 2)

    def test_get_user_progress(self):
        a1 = AttemptRepository.create(user=self.user, symbol=self.symbol_a)
        a1.is_correct = True
        a1.status = "completed"
        a1.save()
        a2 = AttemptRepository.create(user=self.user, symbol=self.symbol_a)
        a2.is_correct = False
        a2.status = "completed"
        a2.save()

        progress = AttemptRepository.get_user_progress(self.user)
        entry = next(p for p in progress if p["symbol__letter"] == "A")
        self.assertEqual(entry["total"], 2)
        self.assertEqual(entry["correct"], 1)


class SubmitAttemptServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123x")
        Symbol.objects.create(letter="A", name="Alpha")

    def test_submit_attempt_creates_and_predicts(self):
        attempt = submit_attempt(
            user=self.user,
            symbol_letter="A",
            image_data="aW1hZ2VkYXRh",
        )

        self.assertIn(attempt.status, ("completed", "failed"))
        self.assertTrue(attempt.image_data)

    def test_submit_attempt_invalid_symbol_raises(self):
        with self.assertRaises(Symbol.DoesNotExist):
            submit_attempt(
                user=self.user,
                symbol_letter="Z",
                image_data="aW1hZ2VkYXRh",
            )


class GetUserProgressServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", password="testpass123x")
        self.symbol = Symbol.objects.create(letter="A", name="Alpha")

    def test_returns_progress_list(self):
        Attempt.objects.create(
            user=self.user, symbol=self.symbol,
            is_correct=True, status="completed",
        )
        progress = get_user_progress(self.user)
        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0]["symbol__letter"], "A")
        self.assertEqual(progress[0]["correct"], 1)


class SymbolViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("testuser", password="testpass123x")
        self.client.force_authenticate(user=self.user)
        Symbol.objects.create(letter="A", name="Alpha")
        Symbol.objects.create(letter="B", name="Bravo")

    def test_list_symbols(self):
        response = self.client.get("/api/symbols/")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_symbol_by_letter(self):
        response = self.client.get("/api/symbols/A/")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["letter"], "A")

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/symbols/")
        self.assertEqual(response.status_code, http_status.HTTP_401_UNAUTHORIZED)


class AttemptViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("testuser", password="testpass123x")
        self.client.force_authenticate(user=self.user)
        self.symbol = Symbol.objects.create(letter="A", name="Alpha")

    def test_create_attempt(self):
        response = self.client.post("/api/attempts/", {
            "symbol_letter": "A",
            "image_data": "aW1hZ2VkYXRh",
        })
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)
        self.assertIn(response.data["status"], ("completed", "failed"))

    def test_list_attempts(self):
        Attempt.objects.create(user=self.user, symbol=self.symbol)
        response = self.client.get("/api/attempts/")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_attempts_only_own(self):
        other_user = User.objects.create_user("other", password="testpass123x")
        Attempt.objects.create(user=other_user, symbol=self.symbol)
        response = self.client.get("/api/attempts/")
        self.assertEqual(len(response.data["results"]), 0)


class ProgressViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("testuser", password="testpass123x")
        self.client.force_authenticate(user=self.user)
        self.symbol = Symbol.objects.create(letter="A", name="Alpha")

    def test_progress_returns_stats(self):
        Attempt.objects.create(
            user=self.user, symbol=self.symbol,
            is_correct=True, status="completed",
        )
        response = self.client.get("/api/progress/")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["symbol_letter"], "A")
