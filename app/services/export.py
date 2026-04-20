import io
import zipfile

import structlog
from db.client import create_storage_client

logger = structlog.get_logger()


async def generate_event_export(
    event_id: str,
    event_title: str | None,
    summary: str | None,
    recordings: list[dict],
) -> bytes:
    """Generate a ZIP file containing event data for export.

    Args:
        event_id: UUID of the event
        event_title: Title of the event
        summary: Generated summary of the story
        recordings: List of recording dicts with audio_url, transcript, recording_type

    Returns:
        ZIP file as bytes
    """
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        title = event_title or "Untitled Story"
        safe_title = _sanitize_filename(title)

        if summary:
            md_content = _generate_markdown(title, summary, recordings)
            zf.writestr(f"{safe_title}.md", md_content)

        artifacts_dir = "artifacts"
        additional_dir = "artifacts/additional"

        initial_story = None
        additional_recordings = []

        for rec in recordings:
            if rec.get("recording_type") == "initial_story":
                initial_story = rec
            else:
                additional_recordings.append(rec)

        if initial_story:
            await _add_recording_to_zip(
                zf, initial_story, artifacts_dir, safe_title
            )

        for i, rec in enumerate(additional_recordings, start=1):
            await _add_recording_to_zip(
                zf, rec, additional_dir, f"follow_up_{i}"
            )

    buffer.seek(0)
    return buffer.getvalue()


async def _add_recording_to_zip(
    zf: zipfile.ZipFile,
    recording: dict,
    directory: str,
    base_name: str,
) -> None:
    """Add a recording's audio and transcript to the ZIP file.

    Args:
        zf: ZipFile object
        recording: Recording dict with audio_url and transcript
        directory: Directory path in ZIP
        base_name: Base filename without extension
    """
    storage_client = create_storage_client()

    audio_url = recording.get("audio_url")
    transcript = recording.get("transcript")

    if audio_url:
        try:
            path_parts = audio_url.split("/audio-recordings/")
            if len(path_parts) >= 2:
                file_path = path_parts[1]
                audio_data = storage_client.storage.from_("audio-recordings").download(
                    file_path
                )
                zf.writestr(f"{directory}/{base_name}.webm", audio_data)
                logger.info(
                    "export_audio_added",
                    event_id=recording.get("event_id"),
                    recording_id=recording.get("id"),
                    filename=f"{base_name}.webm",
                )
        except Exception as e:
            logger.warning(
                "export_audio_failed",
                recording_id=recording.get("id"),
                error=str(e),
            )

    if transcript:
        zf.writestr(f"{directory}/{base_name}.txt", transcript)
        logger.info(
            "export_transcript_added",
            event_id=recording.get("event_id"),
            recording_id=recording.get("id"),
            filename=f"{base_name}.txt",
        )


def _generate_markdown(title: str, summary: str, recordings: list[dict]) -> str:
    """Generate markdown content for the export.

    Args:
        title: Event title
        summary: Generated summary
        recordings: List of recordings

    Returns:
        Markdown formatted string
    """
    md_lines = [
        f"# {title}",
        "",
        "## Summary",
        "",
        summary,
        "",
        "---",
        "",
        "## Recordings",
        "",
    ]

    for rec in recordings:
        rec_type = rec.get("recording_type", "unknown")
        created = rec.get("created_at", "")
        if created:
            md_lines.append(f"- **{rec_type}** - {created}")
        else:
            md_lines.append(f"- **{rec_type}**")

    md_lines.extend([
        "",
        "---",
        "",
        "*Exported from Life Story Agent*",
    ])

    return "\n".join(md_lines)


def _sanitize_filename(name: str) -> str:
    """Sanitize filename by transliterating Unicode to ASCII and removing invalid characters.

    Args:
        name: Original filename

    Returns:
        Sanitized filename (ASCII-only)
    """
    import re

    from unidecode import unidecode

    # First transliterate Unicode characters to ASCII equivalents
    # e.g., "Motocyklowa Odysseja przez Norwegię" → "Motocyklowa Odysseja przez Norwegie"
    # e.g., "Zażółć gęślą jaźń" → "Zazolc gesla jazn"
    name = unidecode(name)

    # Then remove invalid filename characters for Windows/Mac/Linux
    # Also replace commas, periods, and spaces with underscores for cleaner filenames
    name = re.sub(r'[<>:"/\\|?*,]', "_", name)
    name = re.sub(r'\s+', "_", name)
    name = name.strip(".")
    name = name.strip("_")  # strip underscores
    if not name:
        name = "untitled"
    return name[:100]
