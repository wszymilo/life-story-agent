import asyncpg
from typing import Any


class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def fetch_by_email(self, email: str) -> dict[str, Any] | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1", email
            )
            return dict(row) if row else None

    async def upsert(self, id: str, email: str, preferred_language: str = "pl") -> dict[str, Any]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO users (id, email, preferred_language)
                   VALUES ($1, $2, $3)
                   ON CONFLICT (id) DO NOTHING
                   RETURNING *""",
                id, email, preferred_language,
            )
            return dict(row) if row else {}

    async def update_profile(self, user_id: str, data: dict[str, Any]) -> None:
        if not data:
            return
        # NOTE: column names come from pydantic model_dump(exclude_unset=True)
        # or hardcoded dicts — keep them out of raw user input.
        sets = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(data.keys()))
        values = list(data.values())
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"UPDATE users SET {sets} WHERE id = $1",
                user_id, *values,
            )

    async def fetch_language(self, user_id: str) -> str:
        async with self.pool.acquire() as conn:
            row = await conn.fetchval(
                "SELECT preferred_language FROM users WHERE id = $1",
                user_id,
            )
            return row or "pl"

    async def fetch_relatives(self, user_id: str) -> list[dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM relatives WHERE user_id = $1 ORDER BY created_at",
                user_id,
            )
            return [dict(r) for r in rows]

    async def insert_relative(self, user_id: str, name: str, relationship: str) -> dict[str, Any]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO relatives (user_id, name, relationship) VALUES ($1, $2, $3) RETURNING *",
                user_id, name, relationship,
            )
            return dict(row)

    async def delete_relative(self, relative_id: str, user_id: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM relatives WHERE id = $1 AND user_id = $2",
                relative_id, user_id,
            )
