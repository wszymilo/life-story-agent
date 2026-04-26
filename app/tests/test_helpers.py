"""Tests for DRY helper functions in api/utils.py"""

from datetime import date, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from api.utils import (
    get_event_for_user,
    get_next_sequence_order,
    get_transcripts_from_recordings,
    require_data,
    serialize_update_data,
    validate_recordings_exist,
)
from fastapi import HTTPException


class MockResponse:
    def __init__(self, data):
        self.data = data


class TestRequireData:
    """Tests for require_data utility function (existing)."""

    def test_valid_data_returns_first_item(self):
        """Test that valid list data returns first item."""
        response = MockResponse([{"id": "123", "name": "test"}])
        result = require_data(response, "Not found")
        assert result == {"id": "123", "name": "test"}

    def test_empty_list_raises_404(self):
        """Test that empty list raises 404."""
        response = MockResponse([])
        with pytest.raises(HTTPException) as exc_info:
            require_data(response, "Not found")
        assert exc_info.value.status_code == 404

    def test_none_raises_404(self):
        """Test that None data raises 404."""
        response = MockResponse(None)
        with pytest.raises(HTTPException) as exc_info:
            require_data(response, "Not found")
        assert exc_info.value.status_code == 404

    def test_dict_raises_404(self):
        """Test that dict (error response) raises 404."""
        response = MockResponse({"error": "Something went wrong"})
        with pytest.raises(HTTPException) as exc_info:
            require_data(response, "Not found")
        assert exc_info.value.status_code == 404


class TestSerializeUpdateData:
    """Tests for serialize_update_data helper."""

    def test_returns_empty_dict_for_empty_input(self):
        """Empty dict should return as-is with updated_at."""
        result = serialize_update_data({})
        assert result == {}

    def test_adds_updated_at_timestamp(self):
        """Should add updated_at with current timestamp."""
        result = serialize_update_data({"title": "Test"})
        assert "updated_at" in result
        # Should be a valid ISO timestamp
        datetime.fromisoformat(result["updated_at"])

    def test_serializes_date_object(self):
        """Should convert date objects to ISO strings."""
        input_data = {"title": "Test", "birth_date": date(1950, 6, 15)}
        result = serialize_update_data(input_data)
        assert result["birth_date"] == "1950-06-15"

    def test_serializes_multiple_dates(self):
        """Should handle multiple date fields."""
        input_data = {
            "title": "Test",
            "birth_date": date(1950, 1, 1),
            "event_date": date(1980, 12, 31),
        }
        result = serialize_update_data(input_data)
        assert result["birth_date"] == "1950-01-01"
        assert result["event_date"] == "1980-12-31"

    def test_preserves_non_date_fields(self):
        """Should preserve non-date fields unchanged."""
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
    """Tests for get_transcripts_from_recordings helper."""

    def test_returns_empty_list_for_empty_input(self):
        """Empty list should return empty list."""
        result = get_transcripts_from_recordings([])
        assert result == []

    def test_extracts_single_transcript(self):
        """Should extract transcript from single recording."""
        recordings = [{"transcript": "Hello world"}]
        result = get_transcripts_from_recordings(recordings)
        assert result == ["Hello world"]

    def test_skips_null_transcripts(self):
        """Should skip recordings with null/None transcripts."""
        recordings = [
            {"transcript": "First"},
            {"transcript": None},
            {"transcript": "Second"},
            {},  # No transcript key
        ]
        result = get_transcripts_from_recordings(recordings)
        assert result == ["First", "Second"]

    def test_preserves_order(self):
        """Should preserve order of transcripts."""
        recordings = [
            {"transcript": "First"},
            {"transcript": "Second"},
            {"transcript": "Third"},
        ]
        result = get_transcripts_from_recordings(recordings)
        assert result == ["First", "Second", "Third"]

    def test_handles_missing_transcript_key(self):
        """Should handle recordings without transcript key."""
        recordings = [{"id": "1"}, {"transcript": "Hello"}]
        result = get_transcripts_from_recordings(recordings)
        assert result == ["Hello"]


class TestValidateRecordingsExist:
    """Tests for validate_recordings_exist helper."""

    def test_passes_with_data(self):
        """Should pass when data exists."""
        response = MockResponse([{"id": "1"}])
        # Should not raise
        validate_recordings_exist(response)

    def test_raises_400_for_empty_list(self):
        """Should raise 400 for empty list."""
        response = MockResponse([])
        with pytest.raises(HTTPException) as exc_info:
            validate_recordings_exist(response)
        assert exc_info.value.status_code == 400

    def test_raises_400_for_none(self):
        """Should raise 400 for None data."""
        response = MockResponse(None)
        with pytest.raises(HTTPException) as exc_info:
            validate_recordings_exist(response)
        assert exc_info.value.status_code == 400

    def test_custom_error_message(self):
        """Should use custom error message."""
        response = MockResponse(None)
        with pytest.raises(HTTPException) as exc_info:
            validate_recordings_exist(response, "Custom error")
        assert exc_info.value.detail == "Custom error"


class MockSupabaseClient:
    """Mock Supabase client for testing helper functions."""

    def __init__(self, responses: dict[str, list]):
        self._responses = responses

    def table(self, table_name: str):
        return MockTable(table_name, self._responses.get(table_name, []))


class MockTable:
    def __init__(self, table_name: str, data: list):
        self._table_name = table_name
        self._data = data
        self._filters = []
        self._order_field = None
        self._order_desc = False
        self._limit_value = 1

    def select(self, fields: str):
        return self

    def eq(self, field: str, value: Any):
        self._filters.append((field, value))
        return self

    def is_(self, field: str, value: Any):
        self._filters.append((field, value))
        return self

    def order(self, field: str, desc: bool = False):
        self._order_field = field
        self._order_desc = desc
        return self

    def limit(self, n: int):
        self._limit_value = n
        return self

    def execute(self):
        # Apply filters
        result = list(self._data)
        for field, value in self._filters:
            result = [item for item in result if item.get(field) == value]

        # Apply ordering (descending)
        if self._order_field and result:
            result.sort(key=lambda x: x.get(self._order_field) or 0, reverse=self._order_desc)

        # Apply limit
        if self._limit_value:
            result = result[:self._limit_value]

        return MockResponse(data=result)


class TestGetNextSequenceOrder:
    """Tests for get_next_sequence_order helper."""

    async def test_returns_1_when_no_records(self):
        """Should return 1 when no records exist for event."""
        mock_client = MockSupabaseClient({
            "audio_recordings": [],
        })
        result = await get_next_sequence_order(mock_client, "audio_recordings", "event-123")
        assert result == 1

    async def test_returns_max_plus_1_when_records_exist(self):
        """Should return max sequence + 1 when records exist."""
        mock_client = MockSupabaseClient({
            "audio_recordings": [
                {"event_id": "event-123", "sequence_order": 1},
                {"event_id": "event-123", "sequence_order": 3},
                {"event_id": "event-123", "sequence_order": 2},
            ],
        })
        result = await get_next_sequence_order(mock_client, "audio_recordings", "event-123")
        assert result == 4

    async def test_handles_null_sequence_order(self):
        """Should return 1 when sequence_order is null."""
        mock_client = MockSupabaseClient({
            "audio_recordings": [
                {"event_id": "event-123", "sequence_order": None},
            ],
        })
        result = await get_next_sequence_order(mock_client, "audio_recordings", "event-123")
        assert result == 1

    async def test_handles_empty_response(self):
        """Should return 1 when response has no data."""
        mock_client = MockSupabaseClient({
            "audio_recordings": [],
        })
        result = await get_next_sequence_order(mock_client, "audio_recordings", "event-456")
        assert result == 1


def create_mock_table():
    """Create a mock table with proper chainable interface."""
    mock = MagicMock()

    # Select mock
    select_mock = MagicMock()
    select_mock.select = MagicMock(return_value=select_mock)

    # Build the chain: table -> select -> eq -> eq -> execute
    eq_mock_1 = MagicMock()
    eq_mock_1.eq = MagicMock(return_value=eq_mock_1)
    eq_mock_1.execute = MagicMock()

    select_mock.eq = MagicMock(return_value=eq_mock_1)

    mock.select = MagicMock(return_value=select_mock)
    return mock, eq_mock_1


class TestGetEventForUser:
    """Tests for get_event_for_user helper."""

    def test_returns_event_when_owned(self):
        """Should return event when user owns it."""
        mock_client = MagicMock()

        # Set up mock chain
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq_1 = MagicMock()
        mock_eq_2 = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq_1
        mock_eq_1.eq.return_value = mock_eq_2
        mock_eq_2.execute.return_value = MockResponse([{
            "id": "event-123",
            "user_id": "user-456",
            "title": "My Story",
        }])

        import asyncio
        result = asyncio.run(get_event_for_user(mock_client, "event-123", "user-456"))
        assert result["title"] == "My Story"

    def test_raises_404_when_not_found(self):
        """Should raise 404 when event doesn't exist."""
        mock_client = MagicMock()

        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq_1 = MagicMock()
        mock_eq_2 = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq_1
        mock_eq_1.eq.return_value = mock_eq_2
        mock_eq_2.execute.return_value = MockResponse([])

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_event_for_user(mock_client, "event-123", "user-456"))
        assert exc_info.value.status_code == 404

    def test_raises_404_when_not_owned(self):
        """Should raise 404 when event belongs to different user."""
        mock_client = MagicMock()

        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq_1 = MagicMock()
        mock_eq_2 = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq_1
        mock_eq_1.eq.return_value = mock_eq_2
        mock_eq_2.execute.return_value = MockResponse([])

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_event_for_user(mock_client, "event-123", "user-456"))
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Event not found"
