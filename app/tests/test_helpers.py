from datetime import date, datetime

from api.utils import (
    get_transcripts_from_recordings,
    serialize_update_data,
)


class TestSerializeUpdateData:
    def test_returns_empty_dict_for_empty_input(self):
        result = serialize_update_data({})
        assert result == {}

    def test_adds_updated_at_datetime(self):
        result = serialize_update_data({"title": "Test"})
        assert "updated_at" in result
        assert isinstance(result["updated_at"], datetime)

    def test_preserves_date_object(self):
        input_data = {"title": "Test", "birth_date": date(1950, 6, 15)}
        result = serialize_update_data(input_data)
        assert isinstance(result["birth_date"], date)
        assert result["birth_date"] == date(1950, 6, 15)

    def test_preserves_multiple_dates(self):
        input_data = {
            "title": "Test",
            "birth_date": date(1950, 1, 1),
            "event_date": date(1980, 12, 31),
        }
        result = serialize_update_data(input_data)
        assert result["birth_date"] == date(1950, 1, 1)
        assert result["event_date"] == date(1980, 12, 31)

    def test_preserves_non_date_fields(self):
        input_data = {
            "title": "My Story",
            "status": "draft",
            "place": "Poland",
            "count": 42,
            "active": True,
        }
        result = serialize_update_data(input_data)
        assert result["title"] == "My Story"
        assert result["status"] == "draft"
        assert result["place"] == "Poland"
        assert result["count"] == 42
        assert result["active"] is True


class TestGetTranscriptsFromRecordings:
    def test_returns_empty_list_for_empty_input(self):
        result = get_transcripts_from_recordings([])
        assert result == []

    def test_extracts_single_transcript(self):
        recordings = [{"transcript": "Hello world"}]
        result = get_transcripts_from_recordings(recordings)
        assert result == ["Hello world"]

    def test_skips_null_transcripts(self):
        recordings = [
            {"transcript": "First"},
            {"transcript": None},
            {"transcript": "Second"},
            {},
        ]
        result = get_transcripts_from_recordings(recordings)
        assert result == ["First", "Second"]

    def test_preserves_order(self):
        recordings = [
            {"transcript": "First"},
            {"transcript": "Second"},
            {"transcript": "Third"},
        ]
        result = get_transcripts_from_recordings(recordings)
        assert result == ["First", "Second", "Third"]

    def test_handles_missing_transcript_key(self):
        recordings = [{"id": "1"}, {"transcript": "Hello"}]
        result = get_transcripts_from_recordings(recordings)
        assert result == ["Hello"]
