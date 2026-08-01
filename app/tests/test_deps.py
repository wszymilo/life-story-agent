"""Tests for auth dependency edge cases: pool unavailable and upsert race."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_returns_503_when_db_pool_unavailable(self):
        from api.deps import get_current_user

        mock_request = MagicMock(spec=Request)
        mock_request.app.state.pool = None

        with patch("api.deps.verify_firebase_token", return_value={"email": "u@x.com", "sub": "uid-1"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, authorization="Bearer token")

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_refetches_user_when_upsert_conflicts(self):
        from api.deps import get_current_user

        mock_request = MagicMock(spec=Request)
        mock_request.app.state.pool = MagicMock()

        repo = MagicMock()
        # First fetch: no user → upsert returns {} (concurrent insert won the race)
        # Second fetch (after conflict): returns the row inserted by the other request.
        repo.fetch_by_email = AsyncMock(
            side_effect=[None, {"id": "uid-1", "email": "u@x.com"}]
        )
        repo.upsert = AsyncMock(return_value={})

        with (
            patch("api.deps.verify_firebase_token", return_value={"email": "u@x.com", "sub": "uid-1"}),
            patch("api.deps.get_firebase_user_by_email", return_value=MagicMock()),
            patch("api.deps.UserRepository", return_value=repo),
        ):
            result = await get_current_user(mock_request, authorization="Bearer token")

        assert result.id == "uid-1"
        assert result.email == "u@x.com"
        repo.upsert.assert_awaited_once_with("uid-1", "u@x.com")
        assert repo.fetch_by_email.await_count == 2

    @pytest.mark.asyncio
    async def test_raises_500_if_user_still_missing_after_conflict(self):
        from api.deps import get_current_user

        mock_request = MagicMock(spec=Request)
        mock_request.app.state.pool = MagicMock()

        repo = MagicMock()
        repo.fetch_by_email = AsyncMock(return_value=None)
        repo.upsert = AsyncMock(return_value={})

        with (
            patch("api.deps.verify_firebase_token", return_value={"email": "u@x.com", "sub": "uid-1"}),
            patch("api.deps.get_firebase_user_by_email", return_value=MagicMock()),
            patch("api.deps.UserRepository", return_value=repo),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, authorization="Bearer token")

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
