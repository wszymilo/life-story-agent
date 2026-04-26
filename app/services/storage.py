import asyncio
from typing import Any

import boto3
from botocore.exceptions import ClientError

from api.logging_config import get_logger
from config import get_settings

logger = get_logger()
settings = get_settings()

BUCKET_NAME = settings.audio_bucket


class StorageService:
    """Async wrapper around boto3 S3 operations.

    All sync I/O is offloaded to asyncio.to_thread() to avoid blocking the event loop.
    """

    def __init__(self) -> None:
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            session = boto3.session.Session(region_name=settings.cognito_region)
            self._client = session.client("s3")
        return self._client

    async def download(self, audio_url: str) -> bytes:
        """Download audio data from S3."""
        file_path = _parse_s3_path(audio_url)
        if not file_path:
            raise ValueError(f"Invalid audio URL: {audio_url}")

        client = self._get_client()

        def _download() -> bytes:
            try:
                response = client.get_object(Bucket=BUCKET_NAME, Key=file_path)
                return response["Body"].read()
            except ClientError as e:
                logger.error("storage_download_failed", bucket=BUCKET_NAME, key=file_path, error=str(e))
                raise

        return await asyncio.to_thread(_download)

    async def upload(self, file_path: str, data: bytes, content_type: str = "audio/webm") -> str:
        """Upload data to S3 and return the S3 URL."""
        client = self._get_client()

        def _upload() -> str:
            try:
                client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=file_path,
                    Body=data,
                    ContentType=content_type,
                )
                url = f"https://{BUCKET_NAME}.s3.{settings.cognito_region}.amazonaws.com/{file_path}"
                return url
            except ClientError as e:
                logger.error("storage_upload_failed", bucket=BUCKET_NAME, key=file_path, error=str(e))
                raise

        return await asyncio.to_thread(_upload)

    async def remove(self, audio_url: str) -> None:
        """Remove a single file from S3."""
        file_path = _parse_s3_path(audio_url)
        if not file_path:
            logger.warning("storage_remove_invalid_url", url=audio_url)
            return

        client = self._get_client()

        def _remove() -> None:
            try:
                client.delete_object(Bucket=BUCKET_NAME, Key=file_path)
            except ClientError as e:
                logger.error("storage_remove_failed", bucket=BUCKET_NAME, key=file_path, error=str(e))
                raise

        await asyncio.to_thread(_remove)

    async def remove_many(self, audio_urls: list[str]) -> None:
        """Remove multiple files from S3."""
        paths = []
        for url in audio_urls:
            path = _parse_s3_path(url)
            if path:
                paths.append(path)

        if not paths:
            return

        client = self._get_client()

        def _remove() -> None:
            try:
                objects = [{"Key": path} for path in paths]
                client.delete_objects(
                    Bucket=BUCKET_NAME,
                    Delete={"Objects": objects},
                )
            except ClientError as e:
                logger.error("storage_remove_many_failed", bucket=BUCKET_NAME, error=str(e))
                raise

        await asyncio.to_thread(_remove)


def _parse_s3_path(audio_url: str) -> str | None:
    """Extract S3 key from URL.

    URL format: https://[bucket].s3.[region].amazonaws.com/path/to/file.webm
    or: https://[bucket].s3.amazonaws.com/path/to/file.webm
    Returns the key portion after the bucket name.
    """
    if not audio_url:
        return None

    marker = f"{BUCKET_NAME}/"
    if marker in audio_url:
        parts = audio_url.split(marker)
        if len(parts) >= 2:
            return parts[1]

    if "/" in audio_url:
        url_without_bucket = audio_url.split("/", 3)
        if len(url_without_bucket) >= 4:
            return url_without_bucket[3]

    return None
