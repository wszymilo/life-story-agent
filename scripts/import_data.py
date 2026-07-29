"""One-shot script to import Supabase CSV data and audio files into local Docker PostgreSQL."""

import asyncio
import csv
from datetime import date, datetime
import os
import re
import shutil
from pathlib import Path

import asyncpg

DATA_DIR = Path(__file__).resolve().parent.parent / "lifestoryagent-data"
AUDIO_SOURCE = DATA_DIR / "audio-recordings"
AUDIO_TARGET = Path("/data/audio-recordings")
DB_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://app:devpassword@localhost:5432/life_story_agent",
)

URL_PREFIX = re.compile(
    r"^https://[^/]+/storage/v1/object/public/audio-recordings/"
)

# Columns that contain date values (need conversion from string to Python date)
DATE_COLUMNS = {
    "users": {"birth_date", "created_at", "updated_at"},
    "events": {"time_anchor_date", "created_at", "updated_at"},
    "audio_recordings": {"created_at"},
    "follow_up_questions": {"created_at"},
    "evaluation_results": {"created_at"},
}

# Columns that should be NULL (empty string in CSV), not 'null' literal
NULLABLE_COLUMNS = {
    "users": {"birth_date", "name", "country_of_origin"},
    "events": {"time_anchor", "time_anchor_date", "place", "summary", "trace_id",
               "source_event_ids"},
    "audio_recordings": {"transcript", "duration_seconds"},
    "follow_up_questions": {"audio_url"},
    "evaluation_results": {"factual_accuracy", "coherence", "completeness", "overall_score"},
}

TABLES = [
    "users",
    "events",
    "audio_recordings",
    "follow_up_questions",
    "evaluation_results",
]


def strip_url_prefix(value: str | None) -> str | None:
    if value:
        return URL_PREFIX.sub("", value)
    return value


def parse_value(value: str | None, col: str, table: str):
    """Convert CSV string to appropriate Python type for asyncpg."""
    if value is None or value.strip() == "":
        return None

    value = value.strip()

    # Handle literal 'null' string from Supabase CSV export
    if value.lower() == "null":
        return None

    # Date columns
    if col in {"birth_date", "time_anchor_date"}:
        try:
            parts = value.split("-")
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (IndexError, ValueError):
            return None

    # Timestamp columns
    if col in {"created_at", "updated_at"}:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    # Integer columns
    if col in {"sequence_order", "factual_accuracy", "coherence", "completeness", "overall_score"}:
        try:
            return int(value)
        except ValueError:
            return None

    # Float columns
    if col in {"duration_seconds"}:
        try:
            return float(value)
        except ValueError:
            return None

    # Boolean columns
    if col in {"was_answered"}:
        return value.lower() == "true"

    return value


async def import_csv(conn: asyncpg.Connection, table: str) -> int:
    csv_path = DATA_DIR / f"{table}.csv"
    if not csv_path.exists():
        print(f"  [SKIP] {table} — file not found")
        return 0

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(f"  [SKIP] {table} — empty")
        return 0

    # Transform and parse values
    parsed = []
    for row in rows:
        parsed_row = {}
        for col, val in row.items():
            # Transform audio_url
            if col == "audio_url":
                val = strip_url_prefix(val)
            # Parse to proper Python type
            parsed_row[col] = parse_value(val, col, table)
        parsed.append(parsed_row)

    columns = list(parsed[0].keys())
    records = [tuple(r[c] for c in columns) for r in parsed]

    # Clear existing data (CASCADE handles FK dependencies)
    await conn.execute(f"TRUNCATE TABLE {table} CASCADE")

    await conn.copy_records_to_table(
        table,
        records=records,
        columns=columns,
    )
    print(f"  [OK]   {table} — {len(rows)} rows")
    return len(rows)


async def import_db() -> None:
    print("=== Importing CSV data ===")
    conn = await asyncpg.connect(DB_DSN)
    try:
        total = 0
        # Import in FK-safe order: users → events → audio_recordings → follow_up_questions → evaluation_results
        for table in TABLES:
            count = await import_csv(conn, table)
            total += count
        print(f"Total: {total} rows across {len(TABLES)} tables")
    finally:
        await conn.close()


def import_audio() -> None:
    print("=== Copying audio files ===")
    if not AUDIO_SOURCE.exists():
        print(f"  [SKIP] audio source not found at {AUDIO_SOURCE}")
        return

    AUDIO_TARGET.mkdir(parents=True, exist_ok=True)
    for user_dir in AUDIO_SOURCE.iterdir():
        if not user_dir.is_dir() or user_dir.name.endswith(".zip"):
            continue
        dest = AUDIO_TARGET / user_dir.name
        shutil.copytree(user_dir, dest, dirs_exist_ok=True)
        print(f"  [OK]   {user_dir.name}")

    print("  Done — audio files copied")


async def main() -> None:
    await import_db()
    import_audio()
    print("=== Import complete ===")


if __name__ == "__main__":
    asyncio.run(main())
