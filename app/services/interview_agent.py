
from api.schemas.interview import FollowUpQuestion, TranscriptAnalysis
from config import get_settings
from openai import AsyncOpenAI

LANGUAGE_NAMES = {
    "pl": "Polish",
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "uk": "Ukrainian",
    "ru": "Russian",
}


def get_language_display(code: str) -> str:
    """Convert language code to full name for LLM prompts."""
    return LANGUAGE_NAMES.get(code, code)


async def analyze_transcript(
    transcript: str,
    language: str = "pl"
) -> TranscriptAnalysis:
    """Analyze a transcript to extract time, place, people, and themes.

    Uses GPT-4o-mini with structured outputs for reliable parsing.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    display_language = get_language_display(language)

    system_prompt = f"""You are an expert at analyzing personal stories and life histories.
Your task is to extract structured information from the given transcript.

Analyze the transcript and extract:
1. TIME: Any time references (years, months, seasons, ages like "when I was 10")
2. PLACE: Any locations mentioned (cities, countries, specific places)
3. PEOPLE: Any people mentioned (names, relationships like "my mother", "my teacher")
4. KEY EVENTS: Important events or stories told
5. THEMES: Main themes or topics
6. SUMMARY: A brief summary of what the transcript is about

Be thorough but concise. If something is not mentioned, leave it as null/empty.
The transcript is in {display_language} - extract information accordingly."""

    try:
        response = await client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript}
            ],
            response_format=TranscriptAnalysis,
        )

        return response.choices[0].message.parsed

    except Exception as e:
        err_msg = str(e)
        if "api_key" in err_msg.lower():
            raise RuntimeError("Analysis failed: Invalid API key")
        if "rate_limit" in err_msg.lower():
            raise RuntimeError("Analysis failed: Rate limit exceeded")
        raise RuntimeError(f"Analysis failed: {err_msg}")


async def generate_follow_up_question(
    transcript: str,
    existing_questions: list[str],
    language: str = "pl"
) -> FollowUpQuestion:
    """Generate a contextual follow-up question based on the transcript.

    Uses GPT-4o-mini with structured outputs for reliable parsing.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not configured")

    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    display_language = get_language_display(language)

    existing_questions_text = ""
    if existing_questions:
        existing_questions_text = "\n\nExisting questions already generated (avoid duplication):\n" + "\n".join(f"- {q}" for q in existing_questions)

    system_prompt = f"""You are an expert at generating engaging follow-up questions for life stories.

Your task is to generate ONE thoughtful follow-up question that:
- Is specific to the transcript content (not generic)
- Helps deepen the story (sensory details, emotions, people, places, background context)
- Is open-ended (not yes/no)
- Shows genuine interest in the person's experience

IMPORTANT: Generate diverse questions across different themes. Vary your question type:
- If recent questions were about emotions, ask about SPECIFIC PLACES or PEOPLE mentioned
- If recent questions were about places, ask about the CONTEXT or BACKGROUND
- If recent questions were about people, ask about SENSORY details or specific EVENTS
- Ask about details that would reveal new information, not just feelings

The question should be in {display_language} and conversational in tone.

Return a structured question with:
1. question_text: The actual question to ask
2. question_type: One of: sensory, emotional, people, places, context, detail
3. context: Why this question is relevant
4. target_area: What aspect it explores: place, time, person, emotion, detail, background

Avoid questions that have already been asked (see existing questions below).{existing_questions_text}"""

    try:
        response = await client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript:\n{transcript}"}
            ],
            response_format=FollowUpQuestion,
        )

        return response.choices[0].message.parsed

    except Exception as e:
        err_msg = str(e)
        if "api_key" in err_msg.lower():
            raise RuntimeError("Question generation failed: Invalid API key")
        if "rate_limit" in err_msg.lower():
            raise RuntimeError("Question generation failed: Rate limit exceeded")
        raise RuntimeError(f"Question generation failed: {err_msg}")
