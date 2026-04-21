"""Meta-story generation service.

Generates a combined story from multiple selected events.
"""

import time
from datetime import date, datetime

from api.langfuse_config import log_generation
from api.logging_config import get_logger
from api.utils import get_event_for_user
from config import get_settings
from db.client import get_supabase_client
from openai import AsyncOpenAI

settings = get_settings()
logger = get_logger()


async def generate_meta_story(
    user_id: str,
    event_ids: list[str],
    language: str = "pl",
) -> dict:
    """Generate a meta-story from multiple events.

    Args:
        user_id: The user's ID
        event_ids: List of event IDs to combine
        language: Language code (default: pl)

    Returns:
        Dict with title, summary, time_anchor_date, source_event_ids
    """
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    if len(event_ids) < 2:
        raise ValueError("At least 2 events required")

    if len(event_ids) > settings.max_meta_story_select:
        raise ValueError(f"Maximum {settings.max_meta_story_select} events allowed")

    start_time = time.perf_counter()
    event_count = len(event_ids)

    logger.info(
        "meta_story_started",
        user_id=user_id,
        event_count=event_count,
        language=language,
    )

    supabase = await get_supabase_client()

    events = []
    for event_id in event_ids:
        event = await get_event_for_user(supabase, event_id, user_id)
        if not event:
            logger.warning("meta_story_event_not_found", event_id=event_id)
            raise ValueError(f"Event {event_id} not found")
        if event.get("status") != "complete":
            logger.warning("meta_story_event_not_complete", event_id=event_id, status=event.get("status"))
            raise ValueError(f"Event {event_id} is not complete")
        events.append(event)

    def sort_key(e):
        date_str = e.get("time_anchor_date")
        if date_str:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                pass
        created = e.get("created_at", "")
        if created:
            try:
                return datetime.strptime(created[:10], "%Y-%m-%d")
            except ValueError:
                pass
        return datetime.min

    events.sort(key=sort_key)

    content_parts = []
    for i, event in enumerate(events):
        title = event.get("title") or f"Story {i+1}"
        time_info = event.get("time_anchor_date") or event.get("created_at", "")[:10]

        content_parts.append(f"--- Story {i+1}: {title} ({time_info}) ---")

        if event.get("summary"):
            content_parts.append(f"Summary: {event['summary']}")

        recordings = (
            supabase.table("audio_recordings")
            .select("transcript", "recording_type")
            .eq("event_id", event_id)
            .order("sequence_order")
            .execute()
        )

        transcripts = []
        for rec in recordings.data or []:
            if rec.get("transcript"):
                rec_type = rec.get("recording_type", "unknown")
                transcripts.append(f"[{rec_type}]: {rec['transcript']}")

        if transcripts:
            content_parts.append("Transcripts:")
            for t in transcripts:
                content_parts.append(t)

        content_parts.append("")

    full_content = "\n\n".join(content_parts)

    logger.debug(
        "meta_story_content_prepared",
        event_count=event_count,
        content_length=len(full_content),
    )

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    system_prompt = f"""You are a life story writer. Your task is to create a 
cohesive, flowing narrative that combines multiple short stories into one 
comprehensive life story.

Guidelines:
- CRITICAL: The stories are presented in CHRONOLOGICAL ORDER (oldest to newest).
  You MUST maintain this exact order in your final narrative.
- Each story has a date provided - use these dates to anchor the timeline naturally
- Weave the stories into ONE continuous narrative with smooth transitions between time periods
- Use temporal markers like "In [year]", "Later", "After that", "Years later", etc.
- Use first-person narrative voice
- Preserve key details, emotions, and memories from each source
- Output in {language} language

The output should be a single cohesive story, NOT separate summaries of each story."""

    logger.debug("meta_story_llm_call", step="generate_summary")
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a combined life story from these stories:\n\n{full_content}"}
        ],
        max_tokens=4000,
        temperature=0.7,
    )

    summary = response.choices[0].message.content or ""

    logger.debug("meta_story_llm_call", step="generate_title")
    title_system_prompt = f"""You are a title generator. Create a short, descriptive 
title (max 100 chars) for this life story in {language}."""

    title_response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": title_system_prompt},
            {"role": "user", "content": f"Generate a title for this story:\n\n{summary}"}
        ],
        max_tokens=50,
        temperature=0.5,
    )

    title = title_response.choices[0].message.content or "My Life Story"
    title = title.strip().strip('"').strip("'")[:100]

    source_section = "\n\n---\n\n## Sources\n"
    for i, event in enumerate(events):
        source_title = event.get("title") or f"Story {i+1}"
        source_date = event.get("time_anchor_date") or event.get("created_at", "")[:10]
        source_section += f"{i+1}. {source_title} ({source_date})\n"

    final_summary = summary + source_section

    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "meta_story_completed",
        duration_ms=round(duration_ms, 2),
        event_count=event_count,
        summary_length=len(final_summary),
        title=title[:50],
    )

    log_generation(
        prompt=full_content[:1000],
        completion=final_summary,
        model=settings.openai_model,
        metadata={
            "operation": "meta_story",
            "duration_ms": round(duration_ms, 2),
            "event_count": event_count,
        },
    )

    return {
        "title": title,
        "summary": final_summary,
        "time_anchor_date": date.today().isoformat(),
        "source_event_ids": event_ids,
    }