from typing import Any
import asyncpg


class EvaluationRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def insert(self, data: dict[str, Any]) -> None:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        values = list(data.values())
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO evaluation_results ({columns}) VALUES ({placeholders})",
                *values,
            )

    async def fetch_recent(
        self, eval_type: str | None, limit: int = 10
    ) -> list[dict[str, Any]]:
        async with self.pool.acquire() as conn:
            if eval_type:
                rows = await conn.fetch(
                    "SELECT * FROM evaluation_results WHERE eval_type = $1 ORDER BY created_at DESC LIMIT $2",
                    eval_type, limit,
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM evaluation_results ORDER BY created_at DESC LIMIT $1",
                    limit,
                )
            return [dict(r) for r in rows]

    async def count(self, eval_type: str | None) -> int:
        async with self.pool.acquire() as conn:
            if eval_type:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM evaluation_results WHERE eval_type = $1",
                    eval_type,
                )
            else:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM evaluation_results"
                )
