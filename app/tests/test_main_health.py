"""Tests for backend health-check behavior when the DB pool is unavailable."""

from unittest.mock import patch

import pytest


class TestDbHealth:
    @pytest.mark.asyncio
    async def test_health_ready_reports_error_when_pool_missing(self):
        from main import _check_db_health

        with patch("main.get_pool", side_effect=AssertionError("pool not initialized")):
            result = await _check_db_health()

        assert result["status"] == "error"
        assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_health_ready_connected(self):
        from main import _check_db_health

        from unittest.mock import AsyncMock, MagicMock

        pool = MagicMock()
        conn = AsyncMock()
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=conn)
        cm.__aexit__ = AsyncMock(return_value=None)
        pool.acquire = MagicMock(return_value=cm)
        conn.fetchval = AsyncMock(return_value=7)

        with patch("main.get_pool", return_value=pool):
            result = await _check_db_health()

        assert result["status"] == "connected"
        assert result["user_count"] == 7
