from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status


def require_data(data: Any, detail: str = "Resource not found") -> Any:
    if not isinstance(data, list) or len(data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return data[0]


def serialize_update_data(update_data: dict[str, Any]) -> dict[str, Any]:
    if not update_data:
        return update_data
    update_data["updated_at"] = datetime.now(UTC)
    return update_data


def get_transcripts_from_recordings(recordings: list[dict[str, Any]]) -> list[str | None]:
    return [r.get("transcript") for r in recordings if r.get("transcript")]
