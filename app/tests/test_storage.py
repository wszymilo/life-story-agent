import pytest
from pathlib import Path
from unittest.mock import patch
from services.storage import StorageService, STORAGE_ROOT


class TestStorageService:
    @pytest.mark.asyncio
    async def test_upload_and_download(self, tmp_path: Path):
        svc = StorageService(storage_root=tmp_path)
        file_path = "user/a/b.webm"
        data = b"audio data content"

        result_path = await svc.upload(file_path, data)
        assert result_path == file_path

        downloaded = await svc.download(file_path)
        assert downloaded == data

    @pytest.mark.asyncio
    async def test_download_nonexistent_raises(self, tmp_path: Path):
        svc = StorageService(storage_root=tmp_path)
        with pytest.raises(FileNotFoundError):
            await svc.download("nonexistent/file.webm")

    @pytest.mark.asyncio
    async def test_remove_file(self, tmp_path: Path):
        svc = StorageService(storage_root=tmp_path)
        file_path = "user/a/b.webm"
        await svc.upload(file_path, b"data")
        assert (tmp_path / file_path).exists()

        await svc.remove(file_path)
        assert not (tmp_path / file_path).exists()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_does_not_raise(self, tmp_path: Path):
        svc = StorageService(storage_root=tmp_path)
        await svc.remove("nonexistent/file.webm")

    @pytest.mark.asyncio
    async def test_remove_many(self, tmp_path: Path):
        svc = StorageService(storage_root=tmp_path)
        paths = [f"user/a/{i}.webm" for i in range(3)]
        for p in paths:
            await svc.upload(p, b"data")

        await svc.remove_many(paths)
        for p in paths:
            assert not (tmp_path / p).exists()

    @pytest.mark.asyncio
    async def test_upload_creates_parent_dirs(self, tmp_path: Path):
        svc = StorageService(storage_root=tmp_path)
        deep_path = "deeply/nested/dir/structure/file.webm"
        await svc.upload(deep_path, b"data")
        assert (tmp_path / deep_path).exists()

    @pytest.mark.asyncio
    async def test_overwrite_existing_file(self, tmp_path: Path):
        svc = StorageService(storage_root=tmp_path)
        file_path = "overwrite/file.webm"
        await svc.upload(file_path, b"original")
        await svc.upload(file_path, b"updated")

        downloaded = await svc.download(file_path)
        assert downloaded == b"updated"

    @pytest.mark.asyncio
    async def test_default_storage_root(self):
        svc = StorageService()
        assert str(svc.root) == "/data/audio-recordings"

    def test_uses_configured_audio_storage_path(self):
        with patch("services.storage.get_settings") as mock_settings:
            mock_settings.return_value.audio_storage_path = "/tmp/custom-audio"
            svc = StorageService()
            assert str(svc.root) == "/tmp/custom-audio"

    def test_falls_back_to_container_root_when_unset(self):
        with patch("services.storage.get_settings") as mock_settings:
            mock_settings.return_value.audio_storage_path = ""
            svc = StorageService()
            assert str(svc.root) == str(STORAGE_ROOT)
