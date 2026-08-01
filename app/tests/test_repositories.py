import pytest
from unittest.mock import AsyncMock, MagicMock

from db.repositories.event_repo import EventRepository
from db.repositories.user_repo import UserRepository
from db.repositories.recording_repo import RecordingRepository
from db.repositories.evaluation_repo import EvaluationRepository


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    conn = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=None)
    pool.acquire = MagicMock(return_value=cm)
    return pool


class TestEventRepository:
    @pytest.mark.asyncio
    async def test_fetch_by_id_success(self, mock_pool):
        cm = mock_pool.acquire.return_value
        conn = cm.__aenter__.return_value
        record = {"id": "evt-1", "user_id": "usr-1", "title": "Test"}
        conn.fetchrow = AsyncMock(return_value=record)

        repo = EventRepository(mock_pool)
        result = await repo.fetch_by_id("evt-1", "usr-1")

        assert result is not None
        assert result["id"] == "evt-1"

    @pytest.mark.asyncio
    async def test_fetch_by_id_not_found(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow = AsyncMock(return_value=None)

        repo = EventRepository(mock_pool)
        result = await repo.fetch_by_id("evt-999", "usr-1")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_all_by_user(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetch = AsyncMock(return_value=[
            {"id": "evt-1", "title": "First"},
            {"id": "evt-2", "title": "Second"},
        ])

        repo = EventRepository(mock_pool)
        results = await repo.fetch_all_by_user("usr-1")

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_create(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow = AsyncMock(return_value={"id": "evt-new", "title": "New"})

        repo = EventRepository(mock_pool)
        result = await repo.create({"user_id": "usr-1", "title": "New", "status": "draft"})

        assert result["id"] == "evt-new"

    @pytest.mark.asyncio
    async def test_update(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.execute = AsyncMock()

        repo = EventRepository(mock_pool)
        await repo.update("evt-1", {"title": "Updated"})

        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.execute = AsyncMock()

        repo = EventRepository(mock_pool)
        await repo.delete("evt-1")

        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_trace_id(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchval = AsyncMock(return_value="trace-123")

        repo = EventRepository(mock_pool)
        result = await repo.fetch_trace_id("evt-1")

        assert result == "trace-123"


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_fetch_by_email(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow = AsyncMock(return_value={"id": "usr-1", "email": "test@test.com"})

        repo = UserRepository(mock_pool)
        result = await repo.fetch_by_email("test@test.com")

        assert result is not None
        assert result["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_fetch_language_default(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchval = AsyncMock(return_value=None)

        repo = UserRepository(mock_pool)
        result = await repo.fetch_language("usr-1")

        assert result == "pl"


class TestRecordingRepository:
    @pytest.mark.asyncio
    async def test_next_sequence_order_empty(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchval = AsyncMock(return_value=None)

        repo = RecordingRepository(mock_pool)
        result = await repo.next_sequence_order("audio_recordings", "evt-1")

        assert result == 1

    @pytest.mark.asyncio
    async def test_next_sequence_order_existing(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchval = AsyncMock(return_value=3)

        repo = RecordingRepository(mock_pool)
        result = await repo.next_sequence_order("audio_recordings", "evt-1")

        assert result == 4

    @pytest.mark.asyncio
    async def test_fetch_unanswered_question(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow = AsyncMock(return_value={"id": "q-1", "question_text": "Test?"})

        repo = RecordingRepository(mock_pool)
        result = await repo.fetch_unanswered_question("evt-1")

        assert result is not None
        assert result["id"] == "q-1"


class TestEvaluationRepository:
    @pytest.mark.asyncio
    async def test_count(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchval = AsyncMock(return_value=5)

        repo = EvaluationRepository(mock_pool)
        result = await repo.count(None)

        assert result == 5

    @pytest.mark.asyncio
    async def test_count_filtered(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.fetchval = AsyncMock(return_value=2)

        repo = EvaluationRepository(mock_pool)
        result = await repo.count("summary")

        assert result == 2

    @pytest.mark.asyncio
    async def test_delete_for_event(self, mock_pool):
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.execute = AsyncMock()

        repo = EvaluationRepository(mock_pool)
        await repo.delete_for_event("evt-1")

        conn.execute.assert_called_once()
        call_sql, event_id = conn.execute.call_args[0]
        assert "DELETE FROM evaluation_results" in call_sql
        assert event_id == "evt-1"
