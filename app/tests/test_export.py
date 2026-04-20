"""Tests for export service."""

import pytest
from services.export import _generate_markdown, _sanitize_filename


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_sanitize_removes_invalid_chars(self):
        result = _sanitize_filename("test<>:\"/\\|?*file.txt")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_sanitize_replaces_spaces(self):
        result = _sanitize_filename("test file name")
        assert result == "test_file_name"

    def test_sanitize_trims_dots(self):
        result = _sanitize_filename(".test file.")
        assert result == "test_file"

    def test_sanitize_empty_returns_untitled(self):
        result = _sanitize_filename("   ")
        assert result == "untitled"

    def test_sanitize_truncates_long_names(self):
        long_name = "a" * 200
        result = _sanitize_filename(long_name)
        assert len(result) == 100


class TestGenerateMarkdown:
    """Tests for markdown generation."""

    def test_generates_title(self):
        result = _generate_markdown("My Story", "Summary text", [])
        assert "# My Story" in result

    def test_generates_summary(self):
        result = _generate_markdown("Title", "This is the summary", [])
        assert "This is the summary" in result

    def test_generates_recordings_section(self):
        recordings = [
            {"recording_type": "initial_story", "created_at": "2024-01-01"},
            {"recording_type": "follow_up_response", "created_at": "2024-01-02"},
        ]
        result = _generate_markdown("Title", "Summary", recordings)
        assert "## Recordings" in result
        assert "initial_story" in result
        assert "follow_up_response" in result

    def test_includes_export_footer(self):
        result = _generate_markdown("Title", "Summary", [])
        assert "*Exported from Life Story Agent*" in result


class TestGenerateEventExport:
    """Tests for ZIP export generation."""

    @pytest.mark.asyncio
    async def test_export_generates_zip_bytes(self):
        from services.export import generate_event_export

        recordings = [
            {
                "id": "rec-1",
                "event_id": "event-1",
                "audio_url": None,
                "transcript": "Test transcript",
                "recording_type": "initial_story",
                "created_at": "2024-01-01",
            }
        ]

        result = await generate_event_export(
            event_id="event-1",
            event_title="Test Story",
            summary="Test summary",
            recordings=recordings,
        )

        import io
        import zipfile

        assert result is not None
        buffer = io.BytesIO(result)
        assert zipfile.is_zipfile(buffer)

    @pytest.mark.asyncio
    async def test_export_without_recordings(self):
        from services.export import generate_event_export

        result = await generate_event_export(
            event_id="event-1",
            event_title="Empty Story",
            summary="No recordings",
            recordings=[],
        )

        import io
        import zipfile

        assert result is not None
        buffer = io.BytesIO(result)
        assert zipfile.is_zipfile(buffer)

    @pytest.mark.asyncio
    async def test_export_handles_none_title(self):
        from services.export import generate_event_export

        result = await generate_event_export(
            event_id="event-1",
            event_title=None,
            summary="Summary",
            recordings=[],
        )

        import io
        import zipfile

        assert result is not None
        buffer = io.BytesIO(result)
        assert zipfile.is_zipfile(buffer)
