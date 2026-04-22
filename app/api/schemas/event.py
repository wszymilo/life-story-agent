import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    time_anchor: Optional[str] = None
    time_anchor_date: Optional[date] = None
    place: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    time_anchor: Optional[str] = None
    time_anchor_date: Optional[date] = None
    place: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None


class EventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str]
    time_anchor: Optional[str]
    time_anchor_date: Optional[date]
    place: Optional[str]
    status: str
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AudioRecordingCreate(BaseModel):
    event_id: uuid.UUID
    sequence_order: int = 1
    recording_type: str = "initial_story"
    duration_seconds: Optional[float] = None


class RecordingUpload(BaseModel):
    recording_type: str = "initial_story"
    duration_seconds: Optional[float] = None


class AudioRecordingResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    sequence_order: int
    audio_url: Optional[str]
    transcript: Optional[str]
    recording_type: str
    duration_seconds: Optional[float]
    created_at: datetime
    detail: Optional[str] = None

    model_config = {"from_attributes": True}


class EventWithRecordingsResponse(EventResponse):
    recordings: list[AudioRecordingResponse] = []


class MetaGenerateRequest(BaseModel):
    event_ids: list[str]
