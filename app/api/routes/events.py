import uuid
from typing import Optional

from api.deps import CurrentUser, get_current_user
from api.logging_config import get_logger
from api.schemas.event import (
    AudioRecordingResponse,
    EventCreate,
    EventResponse,
    EventUpdate,
    EventWithRecordingsResponse,
    MetaGenerateRequest,
)
from api.utils import (
    get_event_for_user,
    get_user_language,
    require_data,
    serialize_update_data,
)
from config import get_settings
from db.client import get_supabase_client
from services.storage import StorageService
from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from services.event_completion import complete_event_session
from services.export import _sanitize_filename, generate_event_export
from services.meta_story_generator import generate_meta_story
from services.recording_orchestrator import add_recording_to_event
from services.transcription import transcribe_audio_url

router = APIRouter(prefix="/events", tags=["events"])
logger = get_logger()

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


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


@router.get("/{event_id}", response_model=EventWithRecordingsResponse)
@router.get("/{event_id}/", response_model=EventWithRecordingsResponse)
async def get_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get an event by ID with recordings."""
    logger.info("get_event_request", event_id=str(event_id), user_id=str(current_user.id), method=request.method)
    event_data, recordings = await get_event_with_recordings(request, event_id)
    logger.info("get_event_response", event_id=str(event_id), recordings_count=len(recordings))
    return {**event_data, "recordings": recordings}


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

    serialize_update_data(update_data)

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

    audio_urls = [r["audio_url"] for r in recordings if r.get("audio_url")]
    if audio_urls:
        try:
            storage = StorageService()
            await storage.remove_many(audio_urls)
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


@router.get("/{event_id}/recordings/{recording_id}/audio")
async def stream_recording_audio(
    request: Request,
    event_id: uuid.UUID,
    recording_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Stream audio file for a recording."""
    supabase = await get_supabase_client()

    event = await get_event_for_user(supabase, str(event_id), str(current_user.id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    recording_response = (
        supabase.table("audio_recordings")
        .select("audio_url")
        .eq("id", str(recording_id))
        .eq("event_id", str(event_id))
        .execute()
    )

    if not recording_response.data or len(recording_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    recording = recording_response.data[0]
    audio_url = recording.get("audio_url")

    if not audio_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found",
        )

    try:
        storage = StorageService()
        audio_data = await storage.download(audio_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load audio: {str(e)}",
        )

    return Response(
        content=audio_data,
        media_type="audio/webm",
        headers={
            "Content-Disposition": f'inline; filename="recording_{recording_id}.webm"',
        },
    )


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
    recording_type: str = Form("initial_story"),
    duration_seconds: Optional[float] = Form(None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Add a recording to an event. Accepts audio file via multipart/form-data."""
    logger.info("add_recording_started", event_id=str(event_id), recording_type=recording_type, user_id=str(current_user.id))

    supabase = await get_supabase_client()
    result = await add_recording_to_event(
        supabase=supabase,
        event_id=str(event_id),
        user_id=str(current_user.id),
        file=file,
        recording_type=recording_type,
        duration_seconds=duration_seconds,
    )
    return result


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

    # Get user's preferred language for transcription
    user_language = await get_user_language(supabase, str(current_user.id))

    try:
        transcript = await transcribe_audio_url(recording["audio_url"], language=user_language)
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


@router.post("/{event_id}/complete")
@router.post("/{event_id}/complete/", status_code=status.HTTP_200_OK)
async def complete_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Complete an event session and generate summary.

    Gathers all transcripts and Q&A, generates a grounded summary,
    updates the event with summary and title, sets status to complete.
    """
    supabase = await get_supabase_client()
    result = await complete_event_session(
        supabase=supabase,
        event_id=str(event_id),
        user_id=str(current_user.id),
    )
    return result


@router.get("/{event_id}/export")
async def export_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Export event as a ZIP file containing markdown summary and audio files."""
    supabase = await get_supabase_client()

    event = await get_event_for_user(supabase, str(event_id), str(current_user.id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if event.get("status") != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed events can be exported",
        )

    _, recordings = await get_event_with_recordings(request, event_id)

    recording_data = []
    for rec in recordings:
        recording_data.append({
            "id": str(rec["id"]),
            "event_id": str(event_id),
            "audio_url": rec.get("audio_url"),
            "transcript": rec.get("transcript"),
            "recording_type": rec.get("recording_type"),
            "created_at": rec.get("created_at"),
        })

    try:
        zip_data = await generate_event_export(
            event_id=str(event_id),
            event_title=event.get("title"),
            summary=event.get("summary"),
            recordings=recording_data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate export: {str(e)}",
        )

    title = event.get("title") or "untitled"
    safe_title = _sanitize_filename(title)
    filename = f"{safe_title}.zip"

    return Response(
        content=zip_data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/meta-generate", status_code=status.HTTP_201_CREATED)
async def generate_meta_story_endpoint(
    req: MetaGenerateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate a meta-story from multiple selected events."""
    settings = get_settings()

    if len(req.event_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 events required",
        )

    if len(req.event_ids) > settings.max_meta_story_select:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.max_meta_story_select} events allowed",
        )

    supabase = await get_supabase_client()

    # Get user's preferred language
    user_language = await get_user_language(supabase, str(current_user.id))

    try:
        result = await generate_meta_story(
            user_id=str(current_user.id),
            event_ids=req.event_ids,
            language=user_language,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate meta-story: {str(e)}",
        )

    supabase = await get_supabase_client()

    new_event = {
        "user_id": str(current_user.id),
        "title": result["title"],
        "summary": result["summary"],
        "status": "complete",
        "time_anchor_date": result["time_anchor_date"],
        "source_event_ids": result["source_event_ids"],
    }

    response = supabase.table("events").insert(new_event).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event",
        )

    return {"id": response.data[0]["id"]}
