import asyncpg
from typing import Any


class RecordingRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def fetch_by_event(self, event_id: str) -> list[dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM audio_recordings WHERE event_id = $1 ORDER BY sequence_order",
                event_id,
            )
            return [dict(r) for r in rows]

    async def fetch_by_id(self, recording_id: str) -> dict[str, Any] | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM audio_recordings WHERE id = $1",
                recording_id,
            )
            return dict(row) if row else None

    async def insert(self, data: dict[str, Any]) -> dict[str, Any]:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        values = list(data.values())
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"INSERT INTO audio_recordings ({columns}) VALUES ({placeholders}) RETURNING *",
                *values,
            )
            return dict(row)

    async def update_transcript(self, recording_id: str, transcript: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE audio_recordings SET transcript = $1 WHERE id = $2",
                transcript, recording_id,
            )

    async def fetch_url(self, recording_id: str, event_id: str) -> str | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT audio_url FROM audio_recordings WHERE id = $1 AND event_id = $2",
                recording_id, event_id,
            )

    async def fetch_urls_by_event(self, event_id: str) -> list[str]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT audio_url FROM audio_recordings WHERE event_id = $1 AND audio_url IS NOT NULL",
                event_id,
            )
            return [r["audio_url"] for r in rows if r["audio_url"]]

    async def next_sequence_order(self, table: str, event_id: str) -> int:
        async with self.pool.acquire() as conn:
            val = await conn.fetchval(
                f"SELECT MAX(sequence_order) FROM {table} WHERE event_id = $1",
                event_id,
            )
            return (val + 1) if val is not None else 1

    async def fetch_unanswered_question(self, event_id: str) -> dict[str, Any] | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT * FROM follow_up_questions
                   WHERE event_id = $1 AND audio_url IS NULL AND was_answered = false
                   ORDER BY sequence_order
                   LIMIT 1""",
                event_id,
            )
            return dict(row) if row else None

    async def mark_answered(self, question_id: str, audio_url: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE follow_up_questions SET was_answered = true, audio_url = $1 WHERE id = $2",
                audio_url, question_id,
            )

    async def insert_question(self, data: dict[str, Any]) -> dict[str, Any]:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        values = list(data.values())
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"INSERT INTO follow_up_questions ({columns}) VALUES ({placeholders}) RETURNING *",
                *values,
            )
            return dict(row)

    async def delete_unanswered(self, event_id: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM follow_up_questions WHERE event_id = $1 AND was_answered = false",
                event_id,
            )
