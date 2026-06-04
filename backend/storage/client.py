from urllib.parse import urlparse

from django.conf import settings
from supabase import create_client


class SupabaseStorageClient:
    def __init__(self):
        self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        self._bucket = settings.SUPABASE_STORAGE_BUCKET
        self._allowed_host = urlparse(settings.SUPABASE_URL).hostname

    def upload(self, file_bytes: bytes, path: str, content_type: str = "image/png") -> str:
        bucket = self._client.storage.from_(self._bucket)
        bucket.upload(path, file_bytes, {"content-type": content_type})
        return bucket.get_public_url(path)

    def download(self, url: str) -> bytes:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Only http(s) URLs allowed")
        if (parsed.hostname or "").lower() != self._allowed_host:
            raise ValueError("URL host does not match configured Supabase host")
        return self._client.storage.from_(self._bucket).download(
            parsed.path.split(f"/object/public/{self._bucket}/", 1)[-1]
        )
