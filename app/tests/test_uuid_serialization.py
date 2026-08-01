"""Tests for UUID serialization in Pydantic response models.

asyncpg returns UUID columns as Python uuid.UUID objects, not strings.
Pydantic models must accept uuid.UUID values without raising validation errors.
FastAPI's JSON encoder handles the final UUID → str serialization.
"""

import uuid
from datetime import datetime, timezone

from api.schemas.event import EventResponse, AudioRecordingResponse
from api.schemas.user import RelativeResponse
from api.schemas.evaluation import EvaluationResultResponse


def make_uuid() -> uuid.UUID:
    return uuid.uuid4()


class TestEventResponse:
    def test_accepts_uuid_object_for_id(self):
        uid = make_uuid()
        now = datetime.now(timezone.utc)
        data = {
            "id": uid,
            "user_id": "firebase-uid-123",
            "title": "Test",
            "time_anchor": None,
            "time_anchor_date": None,
            "place": None,
            "status": "draft",
            "summary": None,
            "created_at": now,
            "updated_at": now,
        }
        result = EventResponse(**data)
        assert result.id == uid
        assert isinstance(result.id, uuid.UUID)

    def test_accepts_string_for_id(self):
        uid_str = "f384c035-b58d-4ef3-bb71-5c59a388e111"
        now = datetime.now(timezone.utc)
        data = {
            "id": uid_str,
            "user_id": "firebase-uid-123",
            "title": "Test",
            "time_anchor": None,
            "time_anchor_date": None,
            "place": None,
            "status": "draft",
            "summary": None,
            "created_at": now,
            "updated_at": now,
        }
        result = EventResponse(**data)
        assert str(result.id) == uid_str

    def test_serializes_to_string_in_json_mode(self):
        uid = make_uuid()
        now = datetime.now(timezone.utc)
        data = {
            "id": uid,
            "user_id": "firebase-uid-123",
            "title": "Test",
            "time_anchor": None,
            "time_anchor_date": None,
            "place": None,
            "status": "draft",
            "summary": None,
            "created_at": now,
            "updated_at": now,
        }
        result = EventResponse(**data)
        json_data = result.model_dump(mode="json")
        assert isinstance(json_data["id"], str)
        assert json_data["id"] == str(uid)

    def test_keeps_user_id_as_string(self):
        uid = make_uuid()
        now = datetime.now(timezone.utc)
        data = {
            "id": uid,
            "user_id": "firebase-uid-123",
            "title": None,
            "time_anchor": None,
            "time_anchor_date": None,
            "place": None,
            "status": "draft",
            "summary": None,
            "created_at": now,
            "updated_at": now,
        }
        result = EventResponse(**data)
        assert isinstance(result.user_id, str)
        assert result.user_id == "firebase-uid-123"


class TestAudioRecordingResponse:
    def test_accepts_uuid_objects(self):
        uid = make_uuid()
        event_uid = make_uuid()
        now = datetime.now(timezone.utc)
        data = {
            "id": uid,
            "event_id": event_uid,
            "sequence_order": 1,
            "audio_url": None,
            "transcript": None,
            "recording_type": "initial_story",
            "duration_seconds": None,
            "created_at": now,
        }
        result = AudioRecordingResponse(**data)
        assert result.id == uid
        assert result.event_id == event_uid

    def test_serializes_ids_to_string_in_json_mode(self):
        now = datetime.now(timezone.utc)
        data = {
            "id": make_uuid(),
            "event_id": make_uuid(),
            "sequence_order": 1,
            "audio_url": None,
            "transcript": None,
            "recording_type": "initial_story",
            "duration_seconds": None,
            "created_at": now,
        }
        result = AudioRecordingResponse(**data)
        json_data = result.model_dump(mode="json")
        assert isinstance(json_data["id"], str)
        assert isinstance(json_data["event_id"], str)


class TestRelativeResponse:
    def test_accepts_uuid_for_id(self):
        uid = make_uuid()
        now = datetime.now(timezone.utc)
        data = {
            "id": uid,
            "name": "Mother",
            "relationship": "parent",
            "created_at": now,
        }
        result = RelativeResponse(**data)
        assert result.id == uid
        assert isinstance(result.id, uuid.UUID)

    def test_serializes_id_to_string_in_json_mode(self):
        uid = make_uuid()
        now = datetime.now(timezone.utc)
        data = {
            "id": uid,
            "name": "Mother",
            "relationship": "parent",
            "created_at": now,
        }
        result = RelativeResponse(**data)
        json_data = result.model_dump(mode="json")
        assert isinstance(json_data["id"], str)


class TestEvaluationResultResponse:
    def test_accepts_uuid_objects(self):
        uid = make_uuid()
        event_uid = make_uuid()
        now = datetime.now(timezone.utc)
        data = {
            "id": uid,
            "event_id": event_uid,
            "eval_type": "summary",
            "factual_accuracy": 4,
            "coherence": 5,
            "completeness": 4,
            "overall_score": 4,
            "evaluator_model": "gpt-4o-mini",
            "created_at": now,
        }
        result = EvaluationResultResponse(**data)
        assert result.id == uid
        assert result.event_id == event_uid

    def test_serializes_ids_to_string_in_json_mode(self):
        now = datetime.now(timezone.utc)
        data = {
            "id": make_uuid(),
            "event_id": make_uuid(),
            "eval_type": "summary",
            "factual_accuracy": 4,
            "coherence": 5,
            "completeness": 4,
            "overall_score": 4,
            "evaluator_model": "gpt-4o-mini",
            "created_at": now,
        }
        result = EvaluationResultResponse(**data)
        json_data = result.model_dump(mode="json")
        assert isinstance(json_data["id"], str)
        assert isinstance(json_data["event_id"], str)
