import io
import uuid
from datetime import date, datetime
from typing import Optional

from api.deps import CurrentUser, get_current_user
from api.schemas.event import (
    AudioRecordingResponse,
    EventCreate,
    EventResponse,
    EventUpdate,
)
from api.utils import require_data
from db.client import create_storage_client, get_supabase_client
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from services.transcription import transcribe_audio_data, transcribe_audio_url

router = APIRouter(prefix="/events", tags=["events"])


async def get_event_with_recordings(request: Request, event_id: uuid.UUID):
    supabase = await get_supabase_client()

    event_response = (
        supabase.table("events").select("*").eq("id", str(event_id)).execute()
    )
    event_data = require_data(event_response, "Event not found")

    recordings_response = (
        supabase.table("audio_recordings")
        .select("*")
        .eq("event_id", str(event_id))
        .order("sequence_order")
        .execute()
    )

    return event_data, recordings_response.data


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    request: Request,
    event: EventCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new event."""
    supabase = await get_supabase_client()

    event_data = {
        "user_id": str(current_user.id),
        "title": event.title,
        "time_anchor": event.time_anchor,
        "time_anchor_date": event.time_anchor_date.isoformat()
        if event.time_anchor_date
        else None,
        "place": event.place,
        "status": "draft",
    }

    response = supabase.table("events").insert(event_data).execute()
    require_data(response, "Failed to create event")

    return response.data[0]


@router.get("", response_model=list[EventResponse])
@router.get("/", response_model=list[EventResponse])
async def list_events(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all events for user sorted by time_anchor_date."""
    supabase = await get_supabase_client()

    response = (
        supabase.table("events")
        .select("*")
        .eq("user_id", str(current_user.id))
        .order("time_anchor_date", desc=False)
        .order("created_at", desc=False)
        .execute()
    )

    return response.data


@router.get("/{event_id}", response_model=EventResponse)
@router.get("/{event_id}/", response_model=EventResponse)
async def get_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get an event by ID."""
    event_data, _ = await get_event_with_recordings(request, event_id)
    return event_data


@router.put("/{event_id}", response_model=EventResponse)
@router.put("/{event_id}/", response_model=EventResponse)
async def update_event(
    request: Request,
    event_id: uuid.UUID,
    event_update: EventUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an event."""
    supabase = await get_supabase_client()

    update_data = event_update.model_dump(exclude_unset=True)
    if not update_data:
        event_data, _ = await get_event_with_recordings(request, event_id)
        return event_data

    update_data["updated_at"] = datetime.now().isoformat()

    for key, value in update_data.items():
        if isinstance(value, date):
            update_data[key] = value.isoformat()

    response = (
        supabase.table("events")
        .update(update_data)
        .eq("id", str(event_id))
        .execute()
    )
    require_data(response, "Event not found")

    return response.data[0]


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{event_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete event and cascade delete recordings/questions/audio files."""
    supabase = await get_supabase_client()
    event_id_str = str(event_id)

    recordings_response = (
        supabase.table("audio_recordings")
        .select("audio_url")
        .eq("event_id", event_id_str)
        .execute()
    )
    recordings = recordings_response.data if recordings_response.data else []

    for recording in recordings:
        if recording.get("audio_url"):
            try:
                path_parts = recording["audio_url"].split("/audio-recordings/")
                if len(path_parts) > 1:
                    file_path = path_parts[1]
                    supabase.storage.from_("audio-recordings").remove([file_path])
            except Exception:
                pass

    supabase.table("audio_recordings").delete().eq("event_id", event_id_str).execute()
    supabase.table("follow_up_questions").delete().eq("event_id", event_id_str).execute()
    supabase.table("events").delete().eq("id", event_id_str).execute()


@router.get("/{event_id}/recordings", response_model=list[AudioRecordingResponse])
@router.get("/{event_id}/recordings/", response_model=list[AudioRecordingResponse])
async def get_event_recordings(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get all recordings for an event."""
    _, recordings = await get_event_with_recordings(request, event_id)
    return recordings


@router.post(
    "/{event_id}/recordings", response_model=AudioRecordingResponse, status_code=status.HTTP_201_CREATED
)
@router.post(
    "/{event_id}/recordings/", response_model=AudioRecordingResponse, status_code=status.HTTP_201_CREATED
)
async def add_recording(
    request: Request,
    event_id: uuid.UUID,
    file: UploadFile,
    recording_type: str = "initial_story",
    duration_seconds: Optional[float] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Add a recording to an event. Accepts audio file via multipart/form-data."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file type",
        )

    supabase = await get_supabase_client()

    # Create storage client with extended timeout for large files
    storage_client = create_storage_client(timeout=120)

    audio_bytes = await file.read()
    audio_file = io.BytesIO(audio_bytes)

    file_path = f"{current_user.id}/{event_id}/{uuid.uuid4()}.webm"

    try:
        storage_client.storage.from_("audio-recordings").upload(
            file_path,
            audio_file.getvalue(),
            {"content-type": "audio/webm"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload audio: {str(e)}",
        )

    public_url = storage_client.storage.from_("audio-recordings").get_public_url(file_path)

    # Use service key client to download audio directly for transcription (bucket is private)
    service_supabase = create_storage_client(timeout=120)

    transcript = None
    transcription_error = None
    try:
        audio_data = service_supabase.storage.from_("audio-recordings").download(file_path)
        transcript = await transcribe_audio_data(audio_data, language="pl")
    except Exception as e:
        transcript = None
        transcription_error = str(e)

    max_order_response = (
        supabase.table("audio_recordings")
        .select("sequence_order")
        .eq("event_id", str(event_id))
        .order("sequence_order", desc=True)
        .limit(1)
        .execute()
    )
    sequence_order = 1
    if max_order_response.data and max_order_response.data[0].get("sequence_order"):
        sequence_order = max_order_response.data[0]["sequence_order"] + 1

    recording_data = {
        "event_id": str(event_id),
        "audio_url": public_url,
        "transcript": transcript,
        "sequence_order": sequence_order,
        "recording_type": recording_type,
        "duration_seconds": duration_seconds,
    }

    response = supabase.table("audio_recordings").insert(recording_data).execute()
    require_data(response, "Failed to create recording")

    # If this is a follow-up response, mark the question as answered
    if recording_type == "follow_up_response":
        current_question = (
            supabase.table("follow_up_questions")
            .select("id")
            .eq("event_id", str(event_id))
            .is_("audio_url", "null")
            .eq("was_answered", False)
            .order("sequence_order", desc=False)
            .limit(1)
            .execute()
        )
        if current_question.data:
            supabase.table("follow_up_questions").update(
                {"was_answered": True, "audio_url": public_url}
            ).eq("id", current_question.data[0]["id"]).execute()

    if transcription_error:
        recording_with_detail = {
            "id": response.data[0]["id"],
            "event_id": response.data[0]["event_id"],
            "audio_url": response.data[0]["audio_url"],
            "transcript": None,
            "recording_type": response.data[0]["recording_type"],
            "sequence_order": response.data[0]["sequence_order"],
            "duration_seconds": response.data[0].get("duration_seconds"),
            "created_at": response.data[0]["created_at"],
            "detail": "Transcription failed. Your recording is saved."
        }
        return recording_with_detail

    return response.data[0]


@router.post(
    "/recordings/{recording_id}/transcribe", response_model=AudioRecordingResponse
)
@router.post(
    "/recordings/{recording_id}/transcribe/", response_model=AudioRecordingResponse
)
async def retry_transcribe(
    request: Request,
    recording_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Retry transcription for an existing recording."""
    supabase = await get_supabase_client()

    recording_response = (
        supabase.table("audio_recordings")
        .select("*")
        .eq("id", str(recording_id))
        .execute()
    )

    # Handle edge case where response.data exists but is not a list
    if not recording_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    if not isinstance(recording_response.data, list) or len(recording_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    recording = recording_response.data[0]

    if not recording.get("audio_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording has no audio file",
        )

    try:
        transcript = await transcribe_audio_url(recording["audio_url"], language="pl")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )

    update_response = (
        supabase.table("audio_recordings")
        .update({"transcript": transcript})
        .eq("id", str(recording_id))
        .execute()
    )

    return update_response.data[0]
