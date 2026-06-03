from django.conf import settings
from supabase import create_client


class SupabaseStorageClient:
    def __init__(self):
        self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        self._bucket = settings.SUPABASE_STORAGE_BUCKET

    def upload(self, file_bytes: bytes, path: str, content_type: str = "image/png") -> str:
        bucket = self._client.storage.from_(self._bucket)
        bucket.upload(path, file_bytes, {"content-type": content_type})
        return bucket.get_public_url(path)
