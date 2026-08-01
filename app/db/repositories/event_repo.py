import asyncpg
from typing import Any


class EventRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def fetch_by_id(self, event_id: str, user_id: str) -> dict[str, Any] | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM events WHERE id = $1 AND user_id = $2",
                event_id, user_id,
            )
            return dict(row) if row else None

    async def fetch_all_by_user(self, user_id: str) -> list[dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM events
                   WHERE user_id = $1
                   ORDER BY time_anchor_date, created_at""",
                user_id,
            )
            return [dict(r) for r in rows]

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        values = list(data.values())
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"INSERT INTO events ({columns}) VALUES ({placeholders}) RETURNING *",
                *values,
            )
            return dict(row)

    async def update(self, event_id: str, data: dict[str, Any]) -> None:
        if not data:
            return
        # NOTE: column names come from pydantic model_dump(exclude_unset=True)
        # or hardcoded dicts — keep them out of raw user input.
        sets = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(data.keys()))
        values = list(data.values())
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"UPDATE events SET {sets} WHERE id = $1",
                event_id, *values,
            )

    async def delete(self, event_id: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM events WHERE id = $1", event_id)

    async def fetch_trace_id(self, event_id: str) -> str | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT trace_id FROM events WHERE id = $1",
                event_id,
            )
