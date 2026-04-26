import uuid
from datetime import date
from typing import Optional

from api.deps import CurrentUser, get_current_user
from api.langfuse_config import (
    create_trace_id,
    get_langfuse,
    log_score,
    story_trace_context,
)
from api.logging_config import get_logger
from langfuse import propagate_attributes
from api.schemas.event import (
    AudioRecordingResponse,
    CompleteEventRequest,
    EventCreate,
    EventResponse,
    EventUpdate,
    EventWithRecordingsResponse,
    MetaGenerateRequest,
    TranscriptUpdateRequest,
)
from api.utils import (
    get_event_for_user,
    get_user_language,
    require_data,
    serialize_update_data,
)
from config import get_settings
from db.query import get_db
from services.storage import StorageService
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from services.event_completion import complete_event_session
from services.meta_story_generator import generate_meta_story
from services.recording_orchestrator import add_recording_to_event
from services.transcription import transcribe_audio_url

router = APIRouter(prefix="/events", tags=["events"])
logger = get_logger()

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


async def get_event_with_recordings(request: Request, event_id: uuid.UUID):
    db = await get_db()

    event_response = (
        db.table("events").select("*").eq("id", event_id).execute()
    )
    event_data = require_data(event_response, "Event not found")

    recordings_response = (
        db.table("audio_recordings")
        .select("*")
        .eq("event_id", event_id)
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
    db = await get_db()

    event_data = {
        "user_id": current_user.id,
        "title": event.title,
        "time_anchor": event.time_anchor,
        "time_anchor_date": event.time_anchor_date.isoformat()
        if event.time_anchor_date
        else None,
        "place": event.place,
        "status": "draft",
        "trace_id": create_trace_id(),
    }

    response = db.table("events").insert(event_data).execute()
    require_data(response, "Failed to create event")

    return response.data[0]


@router.get("", response_model=list[EventResponse])
async def list_events(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all events for user sorted by time_anchor_date."""
    db = await get_db()

    response = (
        db.table("events")
        .select("*")
        .eq("user_id", current_user.id)
        .order("time_anchor_date", desc=False)
        .order("created_at", desc=False)
        .execute()
    )

    return response.data


@router.get("/{event_id}", response_model=EventWithRecordingsResponse)
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
async def update_event(
    request: Request,
    event_id: uuid.UUID,
    event_update: EventUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an event."""
    db = await get_db()

    update_data = event_update.model_dump(exclude_unset=True)
    if not update_data:
        event_data, _ = await get_event_with_recordings(request, event_id)
        return event_data

    serialize_update_data(update_data)

    response = (
        db.table("events")
        .update(update_data)
        .eq("id", event_id)
        .execute()
    )
    require_data(response, "Event not found")

    return response.data[0]


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete event and cascade delete recordings/questions/audio files."""
    db = await get_db()

    recordings_response = (
        db.table("audio_recordings")
        .select("audio_url")
        .eq("event_id", event_id)
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

    db.table("evaluation_results").delete().eq("event_id", event_id).execute()
    db.table("audio_recordings").delete().eq("event_id", event_id).execute()
    db.table("follow_up_questions").delete().eq("event_id", event_id).execute()
    db.table("events").delete().eq("id", event_id).execute()

    return {"status": "deleted", "event_id": str(event_id)}


@router.get("/{event_id}/recordings", response_model=list[AudioRecordingResponse])
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
    db = await get_db()

    event = await get_event_for_user(db, str(event_id), str(current_user.id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    recording_response = (
        db.table("audio_recordings")
        .select("audio_url")
        .eq("id", recording_id)
        .eq("event_id", event_id)
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

    db = await get_db()

    event_response = (
        db.table("events")
        .select("trace_id")
        .eq("id", event_id)
        .execute()
    )
    trace_id = None
    if event_response.data:
        trace_id = event_response.data[0].get("trace_id")

    with story_trace_context(trace_id, str(current_user.id)):
        result = await add_recording_to_event(
            db=db,
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
async def retry_transcribe(
    request: Request,
    recording_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Retry transcription for an existing recording."""
    db = await get_db()

    recording_response = (
        db.table("audio_recordings")
        .select("*")
        .eq("id", recording_id)
        .execute()
    )

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

    user_language = await get_user_language(db, str(current_user.id))

    event_response = (
        db.table("events")
        .select("trace_id")
        .eq("id", recording["event_id"])
        .execute()
    )
    trace_id = None
    if event_response.data:
        trace_id = event_response.data[0].get("trace_id")

    try:
        with story_trace_context(trace_id, str(current_user.id)):
            transcript = await transcribe_audio_url(
                recording["audio_url"],
                language=user_language,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )

    update_response = (
        db.table("audio_recordings")
        .update({"transcript": transcript})
        .eq("id", recording_id)
        .execute()
    )

    return update_response.data[0]


@router.put("/recordings/{recording_id}/transcript", response_model=AudioRecordingResponse)
async def update_recording_transcript(
    request: Request,
    recording_id: uuid.UUID,
    body: TranscriptUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update the encrypted transcript for a recording."""
    db = await get_db()

    recording_response = (
        db.table("audio_recordings")
        .select("event_id")
        .eq("id", recording_id)
        .execute()
    )

    if not recording_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    event_id = recording_response.data[0]["event_id"]
    await get_event_for_user(db, event_id, str(current_user.id))

    update_response = (
        db.table("audio_recordings")
        .update({"transcript": body.transcript})
        .eq("id", recording_id)
        .execute()
    )
    require_data(update_response, "Failed to update transcript")

    return update_response.data[0]


@router.post("/{event_id}/complete", status_code=status.HTTP_200_OK)
async def complete_event(
    request: Request,
    event_id: uuid.UUID,
    body: CompleteEventRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Complete an event session and generate summary.

    Client sends decrypted transcripts and Q&A.
    Backend generates summary via LLM and returns plaintext result.
    Client encrypts and stores the result.
    """
    db = await get_db()

    event_response = (
        db.table("events")
        .select("trace_id")
        .eq("id", event_id)
        .execute()
    )
    trace_id = None
    if event_response.data:
        trace_id = event_response.data[0].get("trace_id")

    with story_trace_context(trace_id, str(current_user.id)):
        result = await complete_event_session(
            db=db,
            event_id=str(event_id),
            user_id=str(current_user.id),
            transcripts=body.transcripts,
            questions_and_answers=body.questions_and_answers,
        )

    eval_payload = result.pop("_eval_payload", None)
    if eval_payload:
        from services.evaluation import evaluate_in_background, should_evaluate
        if should_evaluate():
            evaluate_in_background(
                background_tasks,
                event_id=str(event_id),
                eval_type="summary",
                prompt_text="\n\n".join(eval_payload["transcripts"]),
                summary_text=eval_payload["summary"],
                trace_id=trace_id,
            )

    return result


@router.post("/meta-generate")
async def generate_meta_story_endpoint(
    req: MetaGenerateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate a meta-story from multiple decrypted event sources.

    Client sends decrypted sources (title, summary, transcripts).
    Backend generates combined narrative via LLM and returns plaintext.
    Client encrypts result before storing.
    """
    settings = get_settings()

    if len(req.sources) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 sources required",
        )

    if len(req.sources) > settings.max_meta_story_select:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.max_meta_story_select} sources allowed",
        )

    db = await get_db()
    user_language = await get_user_language(db, str(current_user.id))

    langfuse_client = get_langfuse()
    if langfuse_client:
        with langfuse_client.start_as_current_observation(
            name="meta_story",
            as_type="span",
        ):
            with propagate_attributes(
                user_id=str(current_user.id),
                session_id=f"{str(current_user.id)}_{date.today().isoformat()}",
                trace_name="meta_story",
            ):
                try:
                    result = await generate_meta_story(
                        sources=req.sources,
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

                meta_trace_id = langfuse_client.get_current_trace_id()
    else:
        try:
            result = await generate_meta_story(
                sources=req.sources,
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
        meta_trace_id = None

    eval_scores = None
    from services.evaluation import evaluate_output, should_evaluate
    if should_evaluate():
        prompt_text = "\n\n".join(
            f"{s.get('title', '')}\n{s.get('summary', '')}\n" + "\n".join(s.get('transcripts', []))
            for s in req.sources
        )
        eval_result = await evaluate_output(prompt_text, result["summary"], "meta_story")
        if eval_result:
            eval_scores = {
                "factual_accuracy": eval_result.factual_accuracy,
                "coherence": eval_result.coherence,
                "completeness": eval_result.completeness,
                "overall_score": eval_result.overall_score,
            }
            if meta_trace_id:
                log_score(meta_trace_id, "factual_accuracy", eval_result.factual_accuracy or 0, "eval_type=meta_story")
                log_score(meta_trace_id, "coherence", eval_result.coherence or 0, "eval_type=meta_story")
                log_score(meta_trace_id, "completeness", eval_result.completeness or 0, "eval_type=meta_story")
                log_score(meta_trace_id, "overall_score", eval_result.overall_score or 0, "eval_type=meta_story")

    response = {
        "title": result["title"],
        "summary": result["summary"],
    }
    if eval_scores:
        response["_eval_scores"] = eval_scores

    return response
