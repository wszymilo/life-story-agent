from datetime import UTC, date, datetime
from typing import Any

from fastapi import HTTPException, status


def require_data(response: Any, detail: str = "Resource not found") -> Any:
    """Extract first item from Supabase response data.

    Raises 404 if data is missing, empty, or invalid.
    Raises 500 if response has no .data attribute.
    """
    if not hasattr(response, 'data'):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response: missing data attribute"
        )

    data = response.data

    # Handle None, empty list, or non-list data (dict, etc.)
    if not isinstance(data, list) or len(data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return data[0]


# ============================================================================
# DRY Helper Functions
# ============================================================================

def serialize_update_data(update_data: dict[str, Any]) -> dict[str, Any]:
    """Serialize date objects in update data to ISO format strings.

    Converts Python date/dateime objects to ISO format strings for Supabase.
    Mutates and returns the input dict.
    """
    if not update_data:
        return update_data

    # Add updated_at timestamp
    update_data["updated_at"] = datetime.now(UTC).isoformat()

    # Serialize any date objects
    for key, value in update_data.items():
        if isinstance(value, date):
            update_data[key] = value.isoformat()

    return update_data


def get_transcripts_from_recordings(recordings: list[dict[str, Any]]) -> list[str | None]:
    """Extract non-null transcripts from a list of recording dicts.

    Args:
        recordings: List of recording dicts with 'transcript' key

    Returns:
        List of transcript strings (non-null)
    """
    return [r.get("transcript") for r in recordings if r.get("transcript")]


def validate_recordings_exist(recordings_response: Any, error_detail: str = "No recordings found") -> None:
    """Validate that recordings exist for an event.

    Raises HTTPException 400 if no recordings.

    Args:
        recordings_response: Supabase response with .data attribute
        error_detail: Custom error message

    Raises:
        HTTPException: 400 if no recordings found
    """
    if not recordings_response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail,
        )


def get_next_sequence_order(
    supabase_client: Any,
    table_name: str,
    event_id: str,
    id_field: str = "event_id",
) -> int:
    """Get the next sequence order number for an event's records.

    Queries the table for the highest sequence_order for the given event
    and returns one more than that (defaults to 1 if no records exist).

    Args:
        supabase_client: Supabase client instance
        table_name: Name of the table (e.g., 'audio_recordings', 'follow_up_questions')
        event_id: The event ID to query
        id_field: The field name for event_id in the table (default: 'event_id')

    Returns:
        Next sequence order number (int)
    """
    max_order_response = (
        supabase_client.table(table_name)
        .select("sequence_order")
        .eq(id_field, event_id)
        .order("sequence_order", desc=True)
        .limit(1)
        .execute()
    )

    if (
        max_order_response.data
        and max_order_response.data[0].get("sequence_order") is not None
    ):
        return max_order_response.data[0]["sequence_order"] + 1

    return 1


async def get_event_for_user(
    supabase_client: Any,
    event_id: str,
    user_id: str,
) -> dict[str, Any]:
    """Fetch an event with ownership validation.

    Retrieves an event by ID and verifies it belongs to the current user.
    Raises 404 if event doesn't exist or doesn't belong to user.

    Args:
        supabase_client: Supabase client instance
        event_id: UUID of the event
        user_id: UUID of the current user

    Returns:
        Event dict with all fields

    Raises:
        HTTPException: 404 if event not found or not owned by user
    """
    event_response = (
        supabase_client.table("events")
        .select("*")
        .eq("id", event_id)
        .eq("user_id", user_id)
        .execute()
    )

    return require_data(event_response, "Event not found")  # type: ignore[return-value]


async def get_user_language(supabase_client: Any, user_id: str) -> str:
    """Get user's preferred language, defaulting to Polish.

    Args:
        supabase_client: Supabase client instance
        user_id: UUID of the user

    Returns:
        Language code (e.g., 'pl', 'en')
    """
    user_response = (
        supabase_client.table("users")
        .select("preferred_language")
        .eq("id", user_id)
        .execute()
    )
    if user_response.data and user_response.data[0].get("preferred_language"):
        return user_response.data[0]["preferred_language"]
    return "pl"
