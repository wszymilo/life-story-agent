from pathlib import Path
from typing import Optional
import aiofiles

from api.logging_config import get_logger
from config import get_settings

logger = get_logger()

STORAGE_ROOT = Path("/data/audio-recordings")


class StorageService:
    def __init__(self, storage_root: Optional[Path] = None):
        # Default to the configured AUDIO_STORAGE_PATH; fall back to the
        # container volume path when unset.
        self.root = storage_root or Path(get_settings().audio_storage_path or STORAGE_ROOT)

    async def upload(self, file_path: str, data: bytes, content_type: str = "audio/webm") -> str:
        full_path = self.root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)
        return file_path

    async def download(self, audio_path: str) -> bytes:
        full_path = self.root / audio_path
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def remove(self, audio_path: str) -> None:
        (self.root / audio_path).unlink(missing_ok=True)

    async def remove_many(self, audio_paths: list[str]) -> None:
        for path in audio_paths:
            await self.remove(path)
