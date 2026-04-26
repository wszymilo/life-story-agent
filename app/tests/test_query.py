from unittest.mock import AsyncMock, MagicMock

import asyncpg
import pytest

from db.query import (
    Database,
    DeleteBuilder,
    InsertBuilder,
    QueryBuilder,
    QueryResult,
    UpdateBuilder,
)


class TestQueryResult:
    """Unit tests for QueryResult class."""

    def test_rows_returns_list(self):
        """Should return list of rows."""
        mock_record = MagicMock()
        result = QueryResult([mock_record])
        assert len(result.rows) == 1

    def test_rows_returns_empty_for_none(self):
        """Should return empty list when rows is None."""
        result = QueryResult(None)
        assert result.rows == []

    def test_rows_unwraps_single_record(self):
        """Should return list with single record."""
        mock_record = MagicMock(spec=asyncpg.Record)
        result = QueryResult(mock_record)
        assert len(result.rows) == 1

    def test_data_returns_dict_list(self):
        """Should return list of dicts."""
        mock_record = {"id": "123", "name": "Test"}
        result = QueryResult([mock_record])
        assert len(result.data) == 1
        assert result.data[0]["id"] == "123"

    def test_data_returns_empty_for_none(self):
        """Should return empty list when rows is None."""
        result = QueryResult(None)
        assert result.data == []

    def test_require_data_returns_dict(self):
        """Should return first row as dict."""
        mock_record = {"id": "123", "name": "Test"}
        result = QueryResult([mock_record])
        assert result.require_data()["id"] == "123"

    def test_require_data_raises_for_empty(self):
        """Should raise ValueError when no data."""
        result = QueryResult([])
        with pytest.raises(ValueError, match="No data returned"):
            result.require_data()

    def test_require_data_raises_for_none(self):
        """Should raise ValueError when rows is None."""
        result = QueryResult(None)
        with pytest.raises(ValueError, match="No data returned"):
            result.require_data()


class TestQueryBuilder:
    """Unit tests for QueryBuilder class."""

    def _create_mock_pool(self, fetch_result):
        """Create a mock pool with controlled fetch result."""
        pool = MagicMock()
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=fetch_result)
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=conn)
        ctx.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=ctx)
        return pool

    @pytest.mark.asyncio
    async def test_select_star(self):
        """Should build SELECT * query."""
        pool = self._create_mock_pool([{"id": "1", "name": "Test 1"}])
        builder = QueryBuilder("users", pool)
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        assert "SELECT * FROM users" in conn.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_select_specific_columns(self):
        """Should build SELECT col1, col2 query."""
        pool = self._create_mock_pool([])
        builder = QueryBuilder("users", pool)
        builder.select("id, name")
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        assert "SELECT id, name FROM users" in conn.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_eq_filter(self):
        """Should build WHERE clause."""
        pool = self._create_mock_pool([])
        builder = QueryBuilder("users", pool)
        builder.eq("id", "123")
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        call_args = conn.fetch.call_args
        query = call_args[0][0]
        args = conn.fetch.call_args[0][1]
        assert "WHERE id = $1" in query
        assert args == "123"

    @pytest.mark.asyncio
    async def test_multiple_eq_filters(self):
        """Should build multiple WHERE conditions."""
        pool = self._create_mock_pool([])
        builder = QueryBuilder("users", pool)
        builder.eq("status", "active").eq("country", "Poland")
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        query = conn.fetch.call_args[0][0]
        assert "WHERE status = $1 AND country = $2" in query

    @pytest.mark.asyncio
    async def test_order_ascending(self):
        """Should build ORDER BY clause ascending."""
        pool = self._create_mock_pool([])
        builder = QueryBuilder("users", pool)
        builder.order("created_at", desc=False)
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        assert "ORDER BY created_at ASC" in conn.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_order_descending(self):
        """Should build ORDER BY clause descending."""
        pool = self._create_mock_pool([])
        builder = QueryBuilder("users", pool)
        builder.order("sequence_order", desc=True)
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        assert "ORDER BY sequence_order DESC" in conn.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_limit(self):
        """Should build LIMIT clause."""
        pool = self._create_mock_pool([])
        builder = QueryBuilder("users", pool)
        builder.limit(10)
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        assert "LIMIT 10" in conn.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_offset(self):
        """Should build OFFSET clause."""
        pool = self._create_mock_pool([])
        builder = QueryBuilder("users", pool)
        builder.offset(20)
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        assert "OFFSET 20" in conn.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_full_query(self):
        """Should build complete query with all clauses."""
        pool = self._create_mock_pool([])
        builder = QueryBuilder("events", pool)
        builder.select("id, title").eq("user_id", "user-123").order("created_at", desc=True).limit(5)
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        query = conn.fetch.call_args[0][0]
        assert "SELECT id, title FROM events" in query
        assert "WHERE user_id = $1" in query
        assert "ORDER BY created_at DESC" in query
        assert "LIMIT 5" in query


class TestInsertBuilder:
    """Unit tests for InsertBuilder class."""

    def _create_mock_pool(self, fetch_result):
        """Create a mock pool with controlled fetch result."""
        pool = MagicMock()
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=fetch_result)
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=conn)
        ctx.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=ctx)
        return pool

    @pytest.mark.asyncio
    async def test_insert_single_dict(self):
        """Should build INSERT for single dict."""
        pool = self._create_mock_pool([{"id": "new-id", "name": "Test"}])
        builder = InsertBuilder("users", {"name": "Test", "email": "test@example.com"}, pool)
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        query = conn.fetch.call_args[0][0]
        args = conn.fetch.call_args[0][1:]
        assert "INSERT INTO users" in query
        assert "name" in query
        assert "email" in query
        assert len(args) == 2

    @pytest.mark.asyncio
    async def test_insert_multiple_dicts(self):
        """Should build INSERT for list of dicts."""
        pool = self._create_mock_pool([])
        data = [
            {"name": "Test 1", "email": "test1@example.com"},
            {"name": "Test 2", "email": "test2@example.com"},
        ]
        builder = InsertBuilder("users", data, pool)
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        query = conn.fetch.call_args[0][0]
        args = conn.fetch.call_args[0][1:]
        assert "INSERT INTO users" in query
        assert len(args) == 4  # 2 names + 2 emails

    @pytest.mark.asyncio
    async def test_insert_empty_list(self):
        """Should return empty result for empty list."""
        pool = self._create_mock_pool([])
        builder = InsertBuilder("users", [], pool)
        result = await builder.execute()
        assert result.rows == []


class TestUpdateBuilder:
    """Unit tests for UpdateBuilder class."""

    def _create_mock_pool(self, fetch_result):
        """Create a mock pool with controlled fetch result."""
        pool = MagicMock()
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=fetch_result)
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=conn)
        ctx.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=ctx)
        return pool

    @pytest.mark.asyncio
    async def test_update_single_field(self):
        """Should build UPDATE with single field."""
        pool = self._create_mock_pool([{"id": "123", "name": "Updated"}])
        builder = UpdateBuilder("users", {"name": "Updated"}, pool)
        builder.eq("id", "123")
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        query = conn.fetch.call_args[0][0]
        assert "UPDATE users SET" in query
        assert "name = $1" in query
        assert "WHERE id = $2" in query

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self):
        """Should build UPDATE with multiple fields."""
        pool = self._create_mock_pool([])
        builder = UpdateBuilder("users", {"name": "New", "status": "active"}, pool)
        builder.eq("id", "123")
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        query = conn.fetch.call_args[0][0]
        assert "name = $1" in query
        assert "status = $2" in query

    @pytest.mark.asyncio
    async def test_update_returns_data(self):
        """Should return updated rows."""
        pool = self._create_mock_pool([{"id": "123", "name": "Updated"}])
        builder = UpdateBuilder("users", {"name": "Updated"}, pool)
        builder.eq("id", "123")
        result = await builder.execute()
        assert len(result.rows) == 1


class TestDeleteBuilder:
    """Unit tests for DeleteBuilder class."""

    def _create_mock_pool(self):
        """Create a mock pool with controlled execute result."""
        pool = MagicMock()
        conn = AsyncMock()
        conn.execute = AsyncMock(return_value="DELETE 1")
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=conn)
        ctx.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=ctx)
        return pool

    @pytest.mark.asyncio
    async def test_delete_with_filter(self):
        """Should build DELETE with WHERE clause."""
        pool = self._create_mock_pool()
        builder = DeleteBuilder("users", pool)
        builder.eq("id", "123")
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        query = conn.execute.call_args[0][0]
        assert "DELETE FROM users WHERE id = $1" in query

    @pytest.mark.asyncio
    async def test_delete_without_filter(self):
        """Should build DELETE without WHERE (dangerous!)."""
        pool = self._create_mock_pool()
        builder = DeleteBuilder("users", pool)
        await builder.execute()
        conn = pool.acquire.return_value.__aenter__.return_value
        assert "DELETE FROM users" in conn.execute.call_args[0][0]


class TestDatabase:
    """Unit tests for Database class."""

    def test_table_returns_query_builder(self):
        """Should return QueryBuilder for table()."""
        pool = MagicMock()
        db = Database(pool)
        result = db.table("users")
        assert isinstance(result, QueryBuilder)

    def test_insert_returns_insert_builder(self):
        """Should return InsertBuilder for insert()."""
        pool = MagicMock()
        db = Database(pool)
        result = db.insert("users", {"name": "Test"})
        assert isinstance(result, InsertBuilder)

    def test_update_returns_update_builder(self):
        """Should return UpdateBuilder for update()."""
        pool = MagicMock()
        db = Database(pool)
        result = db.update("users", {"name": "Test"})
        assert isinstance(result, UpdateBuilder)

    def test_delete_returns_delete_builder(self):
        """Should return DeleteBuilder for delete()."""
        pool = MagicMock()
        db = Database(pool)
        result = db.delete("users")
        assert isinstance(result, DeleteBuilder)