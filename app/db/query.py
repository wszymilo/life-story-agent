from typing import Any

import asyncpg

from db.client import get_db_pool


class QueryResult:
    def __init__(self, rows: list[asyncpg.Record] | asyncpg.Record | None):
        self._rows = rows

    @property
    def rows(self) -> list[asyncpg.Record]:
        if self._rows is None:
            return []
        if isinstance(self._rows, asyncpg.Record):
            return [self._rows]
        return self._rows

    @property
    def data(self) -> list[dict]:
        if self._rows is None:
            return []
        if isinstance(self._rows, asyncpg.Record):
            return [dict(self._rows)]
        return [dict(row) for row in self._rows]

    def require_data(self) -> dict:
        if not self._rows:
            raise ValueError("No data returned")
        if isinstance(self._rows, asyncpg.Record):
            return dict(self._rows)
        if len(self._rows) == 0:
            raise ValueError("No data returned")
        return dict(self._rows[0])


class QueryBuilder:
    def __init__(self, table: str, pool: asyncpg.Pool):
        self._table = table
        self._pool = pool
        self._select_cols = "*"
        self._filters: list[str] = []
        self._filter_args: tuple[Any, ...] = ()
        self._order_by: str | None = None
        self._limit_val: int | None = None
        self._offset_val: int | None = None

    def select(self, columns: str = "*") -> "QueryBuilder":
        self._select_cols = columns
        return self

    def eq(self, column: str, value: Any) -> "QueryBuilder":
        idx = len(self._filters) + 1
        self._filters.append(f"{column} = ${idx}")
        self._filter_args = (*self._filter_args, value)
        return self

    def is_(self, column: str, value: Any) -> "QueryBuilder":
        idx = len(self._filters) + 1
        if value is None or value == "null":
            self._filters.append(f"{column} IS NULL")
        else:
            self._filters.append(f"{column} = ${idx}")
            self._filter_args = (*self._filter_args, value)
        return self

    def order(self, column: str, desc: bool = False) -> "QueryBuilder":
        direction = "DESC" if desc else "ASC"
        self._order_by = f"{column} {direction}"
        return self

    def limit(self, n: int) -> "QueryBuilder":
        self._limit_val = n
        return self

    def offset(self, n: int) -> "QueryBuilder":
        self._offset_val = n
        return self

    async def execute(self) -> QueryResult:
        query_parts = [f"SELECT {self._select_cols} FROM {self._table}"]
        args = self._filter_args

        if self._filters:
            query_parts.append("WHERE " + " AND ".join(self._filters))

        if self._order_by:
            query_parts.append(f"ORDER BY {self._order_by}")

        if self._limit_val is not None:
            query_parts.append(f"LIMIT {self._limit_val}")

        if self._offset_val is not None:
            query_parts.append(f"OFFSET {self._offset_val}")

        query = " ".join(query_parts)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
        return QueryResult(rows)


class InsertBuilder:
    def __init__(self, table: str, data: dict | list[dict], pool: asyncpg.Pool):
        self._table = table
        self._pool = pool
        self._data = data

    async def execute(self) -> QueryResult:
        if isinstance(self._data, dict):
            cols = list(self._data.keys())
            vals = list(self._data.values())
            param_idx = ", ".join(f"${i+1}" for i in range(len(vals)))
            col_names = ", ".join(cols)
            query = f"INSERT INTO {self._table} ({col_names}) VALUES ({param_idx}) RETURNING *"
        else:
            if not self._data:
                return QueryResult([])
            cols = list(self._data[0].keys())
            col_names = ", ".join(cols)
            rows_sql = []
            args = []
            for row in self._data:
                vals = list(row.values())
                rows_sql.append("(" + ", ".join(f"${len(args) + i + 1}" for i in range(len(vals))) + ")")
                args.extend(vals)
            query = f"INSERT INTO {self._table} ({col_names}) VALUES {', '.join(rows_sql)} RETURNING *"

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
        return QueryResult(rows)


class UpdateBuilder:
    def __init__(self, table: str, data: dict, pool: asyncpg.Pool):
        self._table = table
        self._pool = pool
        self._data = data
        self._filters: list[str] = []
        self._filter_args: tuple[Any, ...] = ()

    def eq(self, column: str, value: Any) -> "UpdateBuilder":
        idx = len(self._filters) + 1
        self._filters.append(f"{column} = ${len(self._data) + idx}")
        self._filter_args = (*self._filter_args, value)
        return self

    async def execute(self) -> QueryResult:
        set_parts = []
        args = []
        for i, (col, val) in enumerate(self._data.items(), 1):
            set_parts.append(f"{col} = ${i}")
            args.append(val)
        query = f"UPDATE {self._table} SET {', '.join(set_parts)}"
        args = args + list(self._filter_args)

        if self._filters:
            query += " WHERE " + " AND ".join(self._filters)

        query += " RETURNING *"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
        return QueryResult(rows)


class DeleteBuilder:
    def __init__(self, table: str, pool: asyncpg.Pool):
        self._table = table
        self._pool = pool
        self._filters: list[str] = []
        self._filter_args: tuple[Any, ...] = ()

    def eq(self, column: str, value: Any) -> "DeleteBuilder":
        idx = len(self._filters) + 1
        self._filters.append(f"{column} = ${idx}")
        self._filter_args = (*self._filter_args, value)
        return self

    async def execute(self) -> QueryResult:
        query = f"DELETE FROM {self._table}"
        args = tuple(self._filter_args)

        if self._filters:
            query += " WHERE " + " AND ".join(self._filters)

        async with self._pool.acquire() as conn:
            await conn.execute(query, *args)
        return QueryResult([])


class Database:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    def table(self, name: str) -> QueryBuilder:
        return QueryBuilder(name, self._pool)

    def insert(self, table: str, data: dict | list[dict]) -> InsertBuilder:
        return InsertBuilder(table, data, self._pool)

    def update(self, table: str, data: dict) -> UpdateBuilder:
        return UpdateBuilder(table, data, self._pool)

    def delete(self, table: str) -> DeleteBuilder:
        return DeleteBuilder(table, self._pool)


_db_instance: Database | None = None


async def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        pool = await get_db_pool()
        _db_instance = Database(pool)
    return _db_instance


async def close_db() -> None:
    global _db_instance
    _db_instance = None
