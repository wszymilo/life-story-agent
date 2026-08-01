from fastapi import Request
from app.db.repositories import (
    UserRepository,
    EventRepository,
    RecordingRepository,
    EvaluationRepository,
)


def get_user_repo(request: Request) -> UserRepository:
    return UserRepository(request.app.state.pool)


def get_event_repo(request: Request) -> EventRepository:
    return EventRepository(request.app.state.pool)


def get_recording_repo(request: Request) -> RecordingRepository:
    return RecordingRepository(request.app.state.pool)


def get_evaluation_repo(request: Request) -> EvaluationRepository:
    return EvaluationRepository(request.app.state.pool)
