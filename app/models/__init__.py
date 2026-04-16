import uuid
from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseModel(DeclarativeBase):
    pass


class EventStatus(str, PyEnum):
    DRAFT = "draft"
    COMPLETE = "complete"


class RecordingType(str, PyEnum):
    INITIAL_STORY = "initial_story"
    FOLLOW_UP_RESPONSE = "follow_up_response"


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Relative(BaseModel):
    __tablename__ = "relatives"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    relationship: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Event(BaseModel):
    __tablename__ = "events"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    time_anchor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    time_anchor_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    place: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), default=EventStatus.DRAFT)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AudioRecording(BaseModel):
    __tablename__ = "audio_recordings"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE")
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    audio_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recording_type: Mapped[RecordingType] = mapped_column(Enum(RecordingType), nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class FollowUpQuestion(BaseModel):
    __tablename__ = "follow_up_questions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE")
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    was_answered: Mapped[bool] = mapped_column(Boolean, default=False)
    audio_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# Relationships defined separately to avoid forward reference issues
User.relatives = relationship(
    "Relative", back_populates="user", cascade="all, delete-orphan", viewonly=True
)
User.events = relationship(
    "Event", back_populates="user", cascade="all, delete-orphan", viewonly=True
)
Event.user = relationship("User", back_populates="events", viewonly=True)
Event.recordings = relationship(
    "AudioRecording", back_populates="event", cascade="all, delete-orphan", viewonly=True
)
Event.follow_up_questions = relationship(
    "FollowUpQuestion", back_populates="event", cascade="all, delete-orphan", viewonly=True
)
AudioRecording.event = relationship("Event", back_populates="recordings", viewonly=True)
FollowUpQuestion.event = relationship("Event", back_populates="follow_up_questions", viewonly=True)
