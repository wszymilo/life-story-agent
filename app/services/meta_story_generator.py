"""Meta-story generation service.

Generates a combined story from multiple selected events.
"""

import time

from api.langfuse_config import log_generation
from api.logging_config import get_logger
from config import get_settings
from openai import AsyncOpenAI

settings = get_settings()
logger = get_logger()


async def generate_meta_story(
    sources: list[dict],
    language: str = "pl",
) -> dict:
    """Generate a meta-story from multiple event sources.

    Args:
        sources: List of source dicts with title, summary, date, transcripts
        language: Language code (default: pl)

    Returns:
        Dict with title, summary
    """
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    if len(sources) < 2:
        raise ValueError("At least 2 sources required")

    if len(sources) > settings.max_meta_story_select:
        raise ValueError(f"Maximum {settings.max_meta_story_select} sources allowed")

    start_time = time.perf_counter()
    source_count = len(sources)

    logger.info(
        "meta_story_started",
        source_count=source_count,
        language=language,
    )

    content_parts = []
    for i, source in enumerate(sources):
        title = source.get("title") or f"Story {i+1}"
        time_info = source.get("date") or ""

        content_parts.append(f"--- Story {i+1}: {title} ({time_info}) ---")

        if source.get("summary"):
            content_parts.append(f"Summary: {source['summary']}")

        transcripts = source.get("transcripts", [])
        if transcripts:
            content_parts.append("Transcripts:")
            for t in transcripts:
                content_parts.append(t)

        content_parts.append("")

    full_content = "\n\n".join(content_parts)

    logger.debug(
        "meta_story_content_prepared",
        source_count=source_count,
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
    for i, source in enumerate(sources):
        source_title = source.get("title") or f"Story {i+1}"
        source_date = source.get("date") or ""
        source_section += f"{i+1}. {source_title} ({source_date})\n"

    final_summary = summary + source_section

    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "meta_story_completed",
        duration_ms=round(duration_ms, 2),
        source_count=source_count,
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
            "source_count": source_count,
        },
    )

    return {
        "title": title,
        "summary": final_summary,
    }
