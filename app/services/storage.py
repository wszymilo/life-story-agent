import asyncio
from typing import Any

from api.logging_config import get_logger
from db.client import create_storage_client

logger = get_logger()
BUCKET_NAME = "audio-recordings"


def _parse_storage_path(audio_url: str) -> str | None:
    """Extract storage file path from a Supabase Storage public URL.

    URL format: https://...supabase.co/storage/v1/object/public/audio-recordings/path/to/file.webm
    Returns the path portion after the bucket name.
    """
    if not audio_url:
        return None
    marker = f"/{BUCKET_NAME}/"
    parts = audio_url.split(marker)
    if len(parts) < 2:
        return None
    return parts[1]


class StorageService:
    """Async wrapper around Supabase Storage operations.

    All sync I/O is offloaded to asyncio.to_thread() to avoid blocking the event loop.
    """

    def __init__(self) -> None:
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = create_storage_client(timeout=120)
        return self._client

    async def download(self, audio_url: str) -> bytes:
        """Download audio data from a Supabase Storage URL."""
        file_path = _parse_storage_path(audio_url)
        if not file_path:
            raise ValueError(f"Invalid audio URL: {audio_url}")

        client = self._get_client()

        def _download() -> bytes:
            return client.storage.from_(BUCKET_NAME).download(file_path)

        return await asyncio.to_thread(_download)

    async def upload(self, file_path: str, data: bytes, content_type: str = "audio/webm") -> str:
        """Upload data to Supabase Storage and return the public URL."""
        client = self._get_client()

        def _upload() -> None:
            client.storage.from_(BUCKET_NAME).upload(
                file_path,
                data,
                {"content-type": content_type},
            )

        await asyncio.to_thread(_upload)

        def _get_public_url() -> str:
            return client.storage.from_(BUCKET_NAME).get_public_url(file_path)

        return await asyncio.to_thread(_get_public_url)

    async def remove(self, audio_url: str) -> None:
        """Remove a single file from Supabase Storage."""
        file_path = _parse_storage_path(audio_url)
        if not file_path:
            logger.warning("storage_remove_invalid_url", url=audio_url)
            return

        client = self._get_client()

        def _remove() -> None:
            client.storage.from_(BUCKET_NAME).remove([file_path])

        await asyncio.to_thread(_remove)

    async def remove_many(self, audio_urls: list[str]) -> None:
        """Remove multiple files from Supabase Storage."""
        paths = []
        for url in audio_urls:
            path = _parse_storage_path(url)
            if path:
                paths.append(path)

        if not paths:
            return

        client = self._get_client()

        def _remove() -> None:
            client.storage.from_(BUCKET_NAME).remove(paths)

        await asyncio.to_thread(_remove)
