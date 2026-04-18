import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.deps import CurrentUser
from httpx import ASGITransport, AsyncClient


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
        "transcript": None,
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


@pytest.fixture
async def async_client():
    from main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_supabase_user(mock_user_data):
    mock = AsyncMock()
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MockResponse(
        data=[mock_user_data]
    )
    return mock


class MockResponse:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


@pytest.fixture
def mock_supabase():
    def _mock(table_name):
        mock_table = AsyncMock()

        if table_name == "users":
            mock_table.select.return_value.eq.return_value.execute.return_value = MockResponse(
                data=[]
            )
            mock_table.update.return_value.eq.return_value.execute.return_value = MockResponse(
                data=[]
            )
        elif table_name == "relatives":
            mock_table.select.return_value.eq.return_value.execute.return_value = MockResponse(
                data=[]
            )
            mock_table.insert.return_value.execute.return_value = MockResponse(data=[])
            mock_table.delete.return_value.eq.return_value.execute.return_value = MockResponse(
                data=[]
            )

        return mock_table

    with patch("api.routes.users.get_supabase_client", new_callable=AsyncMock) as mock:
        mock.return_value = _mock("users")
        yield mock
