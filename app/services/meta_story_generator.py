"""Meta-story generation service.

Generates a combined story from multiple selected events.
"""

import structlog
from datetime import date

from api.utils import get_event_for_user
from config import get_settings
from db.client import get_supabase_client
from openai import AsyncOpenAI

logger = structlog.get_logger()


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
    settings = get_settings()

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    if len(event_ids) < 2:
        raise ValueError("At least 2 events required")

    if len(event_ids) > settings.max_meta_story_select:
        raise ValueError(f"Maximum {settings.max_meta_story_select} events allowed")

    supabase = await get_supabase_client()

    events = []
    for event_id in event_ids:
        event = await get_event_for_user(supabase, event_id, user_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        if event.get("status") != "complete":
            raise ValueError(f"Event {event_id} is not complete")
        events.append(event)

    events.sort(
        key=lambda e: e.get("time_anchor_date") or e.get("created_at", "")
    )

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

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    system_prompt = f"""You are a life story writer. Your task is to create a 
cohesive, flowing narrative that combines multiple short stories into one 
comprehensive life story.

Guidelines:
- Weave the stories into a single narrative with natural transitions
- Maintain the chronological order of events
- Use first-person narrative voice
- Preserve key details, emotions, and memories from each source
- Create a compelling, readable story that flows naturally
- Output in {language} language

The output should be a single cohesive story, not a list or collection 
of separate summaries."""

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

    return {
        "title": title,
        "summary": final_summary,
        "time_anchor_date": date.today().isoformat(),
        "source_event_ids": event_ids,
    }