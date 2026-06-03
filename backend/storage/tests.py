from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from .client import SupabaseStorageClient


@override_settings(
    SUPABASE_URL="https://test.supabase.co",
    SUPABASE_SERVICE_KEY="test-key",
    SUPABASE_STORAGE_BUCKET="test-bucket",
)
class SupabaseStorageClientTest(TestCase):
    @patch("storage.client.create_client")
    def test_upload_returns_public_url(self, mock_create):
        mock_storage = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.upload.return_value = None
        mock_bucket.get_public_url.return_value = "https://test.supabase.co/storage/v1/object/public/test-bucket/test.png"
        mock_storage.storage.from_.return_value = mock_bucket
        mock_create.return_value = mock_storage

        client = SupabaseStorageClient()
        url = client.upload(b"fake-image-bytes", "test.png", "image/png")

        self.assertEqual(url, "https://test.supabase.co/storage/v1/object/public/test-bucket/test.png")
        mock_bucket.upload.assert_called_once_with("test.png", b"fake-image-bytes", {"content-type": "image/png"})
