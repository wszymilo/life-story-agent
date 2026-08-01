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
    serialize_update_data,
)
from config import get_settings
from db.deps import get_evaluation_repo, get_event_repo, get_recording_repo, get_user_repo
from db.repositories import EventRepository, RecordingRepository, UserRepository, EvaluationRepository
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


async def _require_event(
    event_repo: EventRepository,
    event_id: str,
    user_id: str,
) -> dict:
    """Fetch an event owned by user_id or raise 404 (no cross-user access)."""
    event = await event_repo.fetch_by_id(event_id, user_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    request: Request,
    event: EventCreate,
    current_user: CurrentUser = Depends(get_current_user),
    event_repo: EventRepository = Depends(get_event_repo),
):
    event_data = {
        "user_id": str(current_user.id),
        "title": event.title,
        "time_anchor": event.time_anchor,
        "time_anchor_date": event.time_anchor_date
        if event.time_anchor_date
        else None,
        "place": event.place,
        "status": "draft",
        "trace_id": create_trace_id(),
    }
    return await event_repo.create(event_data)


@router.get("", response_model=list[EventResponse])
async def list_events(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    event_repo: EventRepository = Depends(get_event_repo),
):
    return await event_repo.fetch_all_by_user(str(current_user.id))


@router.get("/{event_id}", response_model=EventWithRecordingsResponse)
async def get_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    event_repo: EventRepository = Depends(get_event_repo),
    recording_repo: RecordingRepository = Depends(get_recording_repo),
):
    logger.info("get_event_request", event_id=str(event_id), user_id=str(current_user.id), method=request.method)
    event_id_str = str(event_id)
    event_data = await event_repo.fetch_by_id(event_id_str, str(current_user.id))
    if not event_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    recordings = await recording_repo.fetch_by_event(event_id_str)
    logger.info("get_event_response", event_id=str(event_id), recordings_count=len(recordings))
    return {**event_data, "recordings": recordings}


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    request: Request,
    event_id: uuid.UUID,
    event_update: EventUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    event_repo: EventRepository = Depends(get_event_repo),
    recording_repo: RecordingRepository = Depends(get_recording_repo),
):
    await _require_event(event_repo, str(event_id), str(current_user.id))

    update_data = event_update.model_dump(exclude_unset=True)
    if not update_data:
        event_data = await event_repo.fetch_by_id(str(event_id), str(current_user.id))
        recordings = await recording_repo.fetch_by_event(str(event_id))
        return {**event_data, "recordings": recordings}

    serialize_update_data(update_data)
    await event_repo.update(str(event_id), update_data)
    event_data = await event_repo.fetch_by_id(str(event_id), str(current_user.id))
    return event_data


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    recording_repo: RecordingRepository = Depends(get_recording_repo),
    event_repo: EventRepository = Depends(get_event_repo),
    evaluation_repo: EvaluationRepository = Depends(get_evaluation_repo),
):
    event_id_str = str(event_id)

    await _require_event(event_repo, event_id_str, str(current_user.id))

    audio_paths = await recording_repo.fetch_urls_by_event(event_id_str)
    if audio_paths:
        try:
            storage = StorageService()
            await storage.remove_many(audio_paths)
        except Exception:
            pass

    await evaluation_repo.delete_for_event(event_id_str)
    await event_repo.delete(event_id_str)

    return {"status": "deleted", "event_id": event_id_str}


@router.get("/{event_id}/recordings", response_model=list[AudioRecordingResponse])
async def get_event_recordings(
    request: Request,
    event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    event_repo: EventRepository = Depends(get_event_repo),
    recording_repo: RecordingRepository = Depends(get_recording_repo),
):
    await _require_event(event_repo, str(event_id), str(current_user.id))
    return await recording_repo.fetch_by_event(str(event_id))


@router.get("/{event_id}/recordings/{recording_id}/audio")
async def stream_recording_audio(
    request: Request,
    event_id: uuid.UUID,
    recording_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    recording_repo: RecordingRepository = Depends(get_recording_repo),
    event_repo: EventRepository = Depends(get_event_repo),
):
    event = await event_repo.fetch_by_id(str(event_id), str(current_user.id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    audio_path = await recording_repo.fetch_url(str(recording_id), str(event_id))
    if not audio_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found",
        )

    try:
        storage = StorageService()
        audio_data = await storage.download(audio_path)
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
    event_repo: EventRepository = Depends(get_event_repo),
    recording_repo: RecordingRepository = Depends(get_recording_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    logger.info("add_recording_started", event_id=str(event_id), recording_type=recording_type, user_id=str(current_user.id))

    await _require_event(event_repo, str(event_id), str(current_user.id))

    trace_id = await event_repo.fetch_trace_id(str(event_id))

    with story_trace_context(trace_id, str(current_user.id)):
        result = await add_recording_to_event(
            recording_repo=recording_repo,
            user_repo=user_repo,
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
    recording_repo: RecordingRepository = Depends(get_recording_repo),
    event_repo: EventRepository = Depends(get_event_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    recording = await recording_repo.fetch_by_id(str(recording_id))
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    await _require_event(event_repo, recording["event_id"], str(current_user.id))

    audio_path = recording.get("audio_url")
    if not audio_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording has no audio file",
        )

    user_language = await user_repo.fetch_language(str(current_user.id))

    trace_id = await event_repo.fetch_trace_id(recording["event_id"])

    try:
        with story_trace_context(trace_id, str(current_user.id)):
            transcript = await transcribe_audio_url(
                audio_path,
                language=user_language,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )

    await recording_repo.update_transcript(str(recording_id), transcript)
    updated = await recording_repo.fetch_by_id(str(recording_id))
    return updated


@router.put("/recordings/{recording_id}/transcript", response_model=AudioRecordingResponse)
async def update_recording_transcript(
    request: Request,
    recording_id: uuid.UUID,
    body: TranscriptUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    recording_repo: RecordingRepository = Depends(get_recording_repo),
    event_repo: EventRepository = Depends(get_event_repo),
):
    recording = await recording_repo.fetch_by_id(str(recording_id))
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )

    event = await event_repo.fetch_by_id(recording["event_id"], str(current_user.id))
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    await recording_repo.update_transcript(str(recording_id), body.transcript)
    updated = await recording_repo.fetch_by_id(str(recording_id))
    return updated


@router.post("/{event_id}/complete", status_code=status.HTTP_200_OK)
async def complete_event(
    request: Request,
    event_id: uuid.UUID,
    body: CompleteEventRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    event_repo: EventRepository = Depends(get_event_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    trace_id = await event_repo.fetch_trace_id(str(event_id))

    with story_trace_context(trace_id, str(current_user.id)):
        result = await complete_event_session(
            event_repo=event_repo,
            user_repo=user_repo,
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
    user_repo: UserRepository = Depends(get_user_repo),
):
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

    user_language = await user_repo.fetch_language(str(current_user.id))

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
