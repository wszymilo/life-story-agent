import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.deps import CurrentUser
from httpx import ASGITransport, AsyncClient


# ============================================================================
# Fixtures: Basic Mocks
# ============================================================================

@pytest.fixture
def mock_user_id():
    return uuid.uuid4()


@pytest.fixture
def mock_event_id():
    return uuid.uuid4()


@pytest.fixture
def mock_current_user(mock_user_id):
    return CurrentUser(id=mock_user_id, email="test@example.com")


@pytest.fixture
def mock_user_data(mock_user_id):
    return {
        "id": str(mock_user_id),
        "email": "test@example.com",
        "name": "Test User",
        "birth_date": "1945-06-15",
        "country_of_origin": "Poland",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_event_data(mock_user_id, mock_event_id):
    return {
        "id": str(mock_event_id),
        "user_id": str(mock_user_id),
        "title": "My Life Story",
        "time_anchor": None,
        "time_anchor_date": None,
        "place": None,
        "status": "draft",
        "summary": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_audio_recording_data(mock_event_id):
    return {
        "id": str(uuid.uuid4()),
        "event_id": str(mock_event_id),
        "sequence_order": 1,
        "audio_url": "https://example.com/audio.webm",
        "transcript": "This is a test transcript",
        "recording_type": "initial_story",
        "duration_seconds": 60.0,
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_relatives_data(mock_user_id):
    return [
        {
            "id": str(uuid.uuid4()),
            "user_id": str(mock_user_id),
            "name": "Anna Maria",
            "relationship": "mother",
            "created_at": "2024-01-01T00:00:00Z",
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": str(mock_user_id),
            "name": "Jan Kowalski",
            "relationship": "father",
            "created_at": "2024-01-01T00:00:00Z",
        },
    ]


# ============================================================================
# Mock Response Classes
# ============================================================================

class MockResponse:
    """Mock Supabase response object."""

    def __init__(self, data: Any = None, count: int | None = None):
        self.data = data
        self.count = count


# ============================================================================
# Async Client Fixture for HTTP Tests
# ============================================================================

@pytest.fixture
async def async_client():
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ============================================================================
# Supabase Client Mock Factory
# ============================================================================

class MockSupabaseClient:
    """Mock Supabase client that can be configured per-table."""

    def __init__(self, responses: dict[str, Any] | None = None):
        self._responses = responses or {}
        self.storage = MagicMock()
        self._storage_mock = MagicMock()
        self.storage.from_ = lambda bucket: self._storage_mock

    def table(self, table_name: str) -> "MockTable":
        return MockTable(table_name, self._responses.get(table_name, []))


class MockTable:
    """Mock Supabase table with chainable methods."""

    def __init__(self, table_name: str, response_data: Any):
        self._table_name = table_name
        self._response_data = response_data
        self._filters = []
        self._select_fields = "*"
        self._order_field = None
        self._order_desc = False
        self._limit_value = None

    def select(self, fields: str = "*"):
        self._select_fields = fields
        return self

    def eq(self, field: str, value: Any):
        self._filters.append(("eq", field, value))
        return self

    def is_(self, field: str, value: Any):
        self._filters.append(("is", field, value))
        return self

    def order(self, field: str, desc: bool = False):
        self._order_field = field
        self._order_desc = desc
        return self

    def limit(self, n: int):
        self._limit_value = n
        return self

    def execute(self) -> MockResponse:
        # Simple filtering for mock - in real tests, more sophisticated
        data = self._response_data
        if isinstance(data, list):
            # Apply filters
            for filter_type, field, value in self._filters:
                if filter_type == "eq":
                    data = [item for item in data if item.get(field) == value]
                elif filter_type == "is":
                    data = [item for item in data if item.get(field) is value]
        return MockResponse(data=data)

    def insert(self, data: dict) -> "MockInsert":
        return MockInsert(self._table_name, data, self._response_data)

    def update(self, data: dict) -> "MockUpdate":
        return MockUpdate(self._table_name, data, self._response_data)

    def delete(self) -> "MockDelete":
        return MockDelete(self._table_name, self._filters, self._response_data)


class MockInsert:
    def __init__(self, table_name: str, data: dict, response_data: Any):
        self._table_name = table_name
        self._data = data
        self._response_data = response_data

    def execute(self) -> MockResponse:
        # Return inserted data with generated ID
        result = [{**self._data, "id": str(uuid.uuid4())}]
        return MockResponse(data=result)


class MockUpdate:
    def __init__(self, table_name: str, data: dict, response_data: Any):
        self._table_name = table_name
        self._data = data
        self._response_data = response_data
        self._filters = []

    def eq(self, field: str, value: Any):
        self._filters.append((field, value))
        return self

    def execute(self) -> MockResponse:
        # Return updated data
        return MockResponse(data=[self._data])


class MockDelete:
    def __init__(self, table_name: str, filters: list, response_data: Any):
        self._table_name = table_name
        self._filters = filters
        self._response_data = response_data

    def eq(self, field: str, value: Any):
        self._filters.append((field, value))
        return self

    def execute(self) -> MockResponse:
        return MockResponse(data=[])


@pytest.fixture
def mock_supabase_client(mock_user_data, mock_event_data, mock_audio_recording_data):
    """Create a mock Supabase client with common test data."""
    return MockSupabaseClient({
        "users": [mock_user_data],
        "events": [mock_event_data],
        "audio_recordings": [mock_audio_recording_data],
        "relatives": [],
        "follow_up_questions": [],
    })


@pytest.fixture
def mock_supabase(mock_user_data):
    """Legacy fixture - wraps async mock."""
    mock = AsyncMock()
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MockResponse(
        data=[mock_user_data]
    )
    return mock


# ============================================================================
# Patch Helper for get_supabase_client
# ============================================================================

def create_supabase_mock(responses: dict[str, list]) -> AsyncMock:
    """Factory to create a mocked get_supabase_client that returns configurable responses.

    Usage:
        responses = {
            "events": [{"id": "123", "title": "Test"}],
            "audio_recordings": [{"id": "1", "transcript": "Hello"}],
        }
        with patch("api.routes.events.get_supabase_client", create_supabase_mock(responses)):
            # test code
    """
    mock = AsyncMock()

    def table_side_effect(table_name: str):
        table_mock = MagicMock()

        def select_fields(fields: str = "*"):
            select_mock = MagicMock()

            def eq_filter(field: str, value: Any):
                filter_mock = MagicMock()

                def execute():
                    data = responses.get(table_name, [])
                    # Simple filter
                    filtered = [d for d in data if d.get(field) == value]
                    return MockResponse(data=filtered)

                filter_mock.execute = execute
                return filter_mock

            select_mock.eq = eq_filter
            return select_mock

        table_mock.select = select_fields
        return table_mock

    mock.table = table_side_effect
    return mock
