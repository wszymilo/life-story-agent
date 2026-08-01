"""Route-level tests for event ownership enforcement (no cross-user access)."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from api.deps import CurrentUser, get_current_user
from db.deps import get_evaluation_repo, get_event_repo, get_recording_repo, get_user_repo


def make_event(user_id="user-1"):
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": "Story",
        "time_anchor": None,
        "time_anchor_date": None,
        "place": None,
        "status": "draft",
        "summary": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


def make_recording(event_id):
    return {
        "id": str(uuid.uuid4()),
        "event_id": str(event_id),
        "sequence_order": 1,
        "audio_url": "user/evt/rec.webm",
        "transcript": None,
        "recording_type": "initial_story",
        "duration_seconds": None,
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
async def ctx():
    """Return (client, repos) with mocked auth + repos."""
    from main import app

    event_repo = MagicMock()
    recording_repo = MagicMock()
    user_repo = MagicMock()
    evaluation_repo = MagicMock()
    # Default: event not owned → 404 path
    event_repo.fetch_by_id = AsyncMock(return_value=None)
    recording_repo.fetch_by_id = AsyncMock(return_value=None)
    recording_repo.fetch_urls_by_event = AsyncMock(return_value=[])
    recording_repo.fetch_by_event = AsyncMock(return_value=[])
    evaluation_repo.delete_for_event = AsyncMock()
    event_repo.delete = AsyncMock()
    event_repo.update = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id="user-1", email="u@x.com")
    app.dependency_overrides[get_event_repo] = lambda: event_repo
    app.dependency_overrides[get_recording_repo] = lambda: recording_repo
    app.dependency_overrides[get_user_repo] = lambda: user_repo
    app.dependency_overrides[get_evaluation_repo] = lambda: evaluation_repo

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, (event_repo, recording_repo, user_repo, evaluation_repo)

    app.dependency_overrides.clear()


class TestOwnership404:
    async def test_delete_event_404_when_not_owned(self, ctx):
        client, (event_repo, *_rest) = ctx
        resp = await client.delete(f"/api/events/{uuid.uuid4()}")
        assert resp.status_code == 404
        event_repo.delete.assert_not_called()

    async def test_update_event_404_when_not_owned(self, ctx):
        client, (event_repo, *_rest) = ctx
        resp = await client.put(f"/api/events/{uuid.uuid4()}", json={"title": "Hacked"})
        assert resp.status_code == 404
        event_repo.update.assert_not_called()

    async def test_get_recordings_404_when_not_owned(self, ctx):
        client, (_event_repo, recording_repo, *_rest) = ctx
        resp = await client.get(f"/api/events/{uuid.uuid4()}/recordings")
        assert resp.status_code == 404
        recording_repo.fetch_by_event.assert_not_called()

    async def test_add_recording_404_when_not_owned(self, ctx):
        client, (_event_repo, recording_repo, *_rest) = ctx
        resp = await client.post(
            f"/api/events/{uuid.uuid4()}/recordings",
            files={"file": ("rec.webm", b"audio", "audio/webm")},
        )
        assert resp.status_code == 404
        recording_repo.insert.assert_not_called()

    async def test_retry_transcribe_404_when_recording_event_not_owned(self, ctx):
        client, (event_repo, recording_repo, *_rest) = ctx
        other_event = uuid.uuid4()
        recording_repo.fetch_by_id = AsyncMock(return_value=make_recording(other_event))
        resp = await client.post(f"/api/events/recordings/{uuid.uuid4()}/transcribe")
        assert resp.status_code == 404
        recording_repo.update_transcript.assert_not_called()

    async def test_store_scores_404_when_event_not_owned(self, ctx):
        client, (_event_repo, _recording_repo, _user_repo, _evaluation_repo) = ctx
        resp = await client.post(
            "/api/evaluations/scores",
            json={
                "event_id": str(uuid.uuid4()),
                "eval_type": "meta_story",
                "factual_accuracy": 5,
                "coherence": 5,
                "completeness": 5,
                "overall_score": 5,
            },
        )
        assert resp.status_code == 404


class TestOwnedOperations:
    async def test_update_event_succeeds_when_owned(self, ctx):
        client, (event_repo, *_rest) = ctx
        event = make_event()
        event_repo.fetch_by_id = AsyncMock(return_value=event)
        event_repo.update = AsyncMock()
        resp = await client.put(
            f"/api/events/{event['id']}", json={"title": "Updated"}
        )
        assert resp.status_code == 200
        event_repo.update.assert_called_once()

    async def test_delete_event_deletes_eval_rows_then_event(self, ctx):
        client, (event_repo, recording_repo, _user_repo, evaluation_repo) = ctx
        event = make_event()
        event_repo.fetch_by_id = AsyncMock(return_value=event)
        recording_repo.fetch_urls_by_event = AsyncMock(return_value=[])
        resp = await client.delete(f"/api/events/{event['id']}")
        assert resp.status_code == 204
        evaluation_repo.delete_for_event.assert_called_once_with(event["id"])
        event_repo.delete.assert_called_once_with(event["id"])
