from datetime import date, datetime
from typing import Any, Optional

from api.schemas.summary import SummaryWithTitle
from config import get_settings
from openai import AsyncOpenAI

MAX_RETRIES = 2


async def generate_summary(
    transcripts: list[str],
    questions_and_answers: list[dict[str, Any]],
    language: str = "pl"
) -> SummaryWithTitle:
    """Generate a grounded summary using Generator-Reviewer pattern.

    Args:
        transcripts: List of transcript strings from recordings
        questions_and_answers: List of dicts with 'question' and 'answer' keys
        language: Language code (default: pl)

    Returns:
        SummaryWithTitle with summary, title, and retry flag
    """
    settings = get_settings()

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    if not transcripts and not questions_and_answers:
        raise ValueError("No content provided to generate summary")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Prepare content for summary
    content_parts = []
    for i, transcript in enumerate(transcripts):
        content_parts.append(f"Recording {i+1}:\n{transcript}")

    for qa in questions_and_answers:
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        if question and answer:
            content_parts.append(f"Q: {question}\nA: {answer}")

    full_content = "\n\n".join(content_parts)

    # Generator step
    summary = await _generate_summary_text(client, full_content, language)

    # Reviewer step - validate grounding
    is_grounded, feedback = await _validate_grounding(
        client, summary, full_content, language
    )

    was_retried = False

    # Retry if not grounded (max 2 retries)
    for retry in range(MAX_RETRIES):
        if is_grounded:
            break

        was_retried = True

        # Regenerate with feedback
        summary = await _generate_summary_with_feedback(
            client, full_content, summary, feedback, language
        )

        # Re-validate
        is_grounded, feedback = await _validate_grounding(
            client, summary, full_content, language
        )

    # Generate title from summary
    title = await _generate_title(client, summary, language)

    # Extract time anchor date from content
    time_anchor_date = await _extract_time_anchor(client, full_content, language)

    return SummaryWithTitle(
        summary=summary,
        title=title,
        was_retried=was_retried,
        time_anchor_date=time_anchor_date
    )


async def _generate_summary_text(
    client: AsyncOpenAI,
    content: str,
    language: str
) -> str:
    """Generator: Create summary from content."""

    system_prompt = f"""You are an expert biographer. Your task is to create a flowing, coherent
narrative summary from the given life story content.

Requirements:
- Write in third person or formal first person ("I recall...", "My life...")
- Include specific details from the source material
- Create a connected narrative (not bullet points)
- Include time and place references when mentioned
- Capture emotions and feelings when expressed
- Language: {language}
- Length: 2-4 paragraphs

Do NOT add any information not present in the source material."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a summary from this life story content:\n\n{content}"}
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        raise RuntimeError(f"Summary generation failed: {str(e)}")


async def _validate_grounding(
    client: AsyncOpenAI,
    summary: str,
    source_content: str,
    language: str
) -> tuple[bool, Optional[str]]:
    """Reviewer: Validate summary is grounded in source material."""

    system_prompt = f"""You are a fact-checker. Your task is to validate that a summary
is accurately grounded in the source material.

Check for:
- Hallucinations (facts not in source)
- Distorted information
- Missing key facts that should be included
- Inaccurate time/place references

Respond with a JSON object:
{{
  "is_grounded": true/false,
  "reason": "brief explanation if not grounded, otherwise 'OK'"
}}

Language: {language}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Source:\n{source_content}\n\nSummary to validate:\n{summary}"}
            ],
            max_tokens=200,
            temperature=0.3,
        )

        content = response.choices[0].message.content or ""

        # Parse response
        is_grounded = "true" in content.lower() and "false" not in content.lower()
        reason = content if not is_grounded else None

        # More sophisticated check
        if not is_grounded:
            if "ok" in content.lower():
                is_grounded = True
                reason = None
            elif '"is_grounded": false' in content.lower():
                is_grounded = False
            elif '"is_grounded": true' in content.lower():
                is_grounded = True
                reason = None

        return is_grounded, reason

    except Exception:
        # On error, assume not grounded to trigger retry
        return False, "Validation error"


async def _generate_summary_with_feedback(
    client: AsyncOpenAI,
    content: str,
    previous_summary: str,
    feedback: str,
    language: str
) -> str:
    """Retry with feedback from reviewer."""

    system_prompt = f"""You are an expert biographer. The previous summary you generated
was rejected because it wasn't properly grounded in the source material.

Feedback from reviewer:
{feedback}

Requirements:
- Write in third person or formal first person
- Include ONLY information from the source material
- Fix any issues mentioned in the feedback
- Language: {language}
- Length: 2-4 paragraphs"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Source:\n{content}\n\nPrevious summary:\n{previous_summary}\n\nCreate a corrected summary:"}
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        raise RuntimeError(f"Summary regeneration failed: {str(e)}")


async def _generate_title(
    client: AsyncOpenAI,
    summary: str,
    language: str
) -> str:
    """Generate a short title from summary."""

    system_prompt = f"""You are a title generator. Create a short, meaningful title
for a life story summary. The title should:

- Be 3-8 words
- Be descriptive but not generic
- Capture the essence of the story
- Language: {language}

Examples:
- "Childhood in Communist Poland"
- "My Journey to America"
- "Life on the Family Farm"
- "Growing Up During War"

Return ONLY the title, nothing else."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a title for:\n{summary}"}
            ],
            max_tokens=50,
            temperature=0.7,
        )

        title = response.choices[0].message.content or ""

        # Clean up title
        title = title.strip().strip('"').strip("'")

        # Fallback if title is empty
        if not title:
            title = "My Life Story"

        return title[:100]  # Limit length

    except Exception:
        return "My Life Story"


async def _extract_time_anchor(
    client: AsyncOpenAI,
    content: str,
    language: str
) -> Optional[date]:
    """Extract primary date from story content for timeline sorting.

    Returns:
        date object if found, None otherwise
    """

    system_prompt = f"""You are a date extraction specialist. Your task is to find the
primary date mentioned in this life story that would serve as a timeline anchor.

Instructions:
- Extract the most significant date mentioned (year required, month/day optional)
- Look for: birth dates, wedding dates, life milestones, specific years mentioned
- For stories about childhood, extract the birth year or year the person was young
- For recent stories, extract the specific year the event occurred
- Return ONLY the date in ISO format (YYYY-MM-DD), nothing else
- If no specific date can be determined, return ONLY "NONE"

Examples:
- "I was born in 1945" → 1945-01-01
- "My wedding was in June 1972" → 1972-06-01
- "In 1950s we lived in Warsaw" → 1950-01-01
- "I started working in 1985" → 1985-01-01

Language: {language}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract the primary date from this story:\n\n{content}"}
            ],
            max_tokens=50,
            temperature=0.3,
        )

        date_str = response.choices[0].message.content or ""
        date_str = date_str.strip().strip('"').strip("'")

        if not date_str or date_str.upper() == "NONE":
            return None

        # Try to parse the date
        for fmt in ["%Y-%m-%d", "%Y-%m", "%Y"]:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                # Validate reasonable year range (1900-2030)
                if 1900 <= parsed.year <= 2030:
                    return parsed
            except ValueError:
                continue

        return None

    except Exception:
        return None
