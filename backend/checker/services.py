import base64
import uuid

from django.contrib.auth.models import User
from django_q.tasks import async_task

from storage.client import SupabaseStorageClient
from .repositories import AttemptRepository, SymbolRepository


def submit_attempt(user: User, symbol_letter: str, image_data: str):
    symbol = SymbolRepository.get_by_letter(symbol_letter)

    image_bytes = base64.b64decode(image_data)

    storage = SupabaseStorageClient()
    path = f"attempts/{user.id}/{uuid.uuid4().hex}.png"
    image_url = storage.upload(image_bytes, path)

    attempt = AttemptRepository.create(
        user=user,
        symbol=symbol,
        image_url=image_url,
    )

    async_task("checker.tasks.process_and_predict", str(attempt.id))

    return attempt


def get_user_progress(user: User) -> list[dict]:
    return AttemptRepository.get_user_progress(user)
