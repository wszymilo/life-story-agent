from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request, status


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_missing_authorization_returns_401(self):
        from api.deps import get_current_user

        mock_request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authorization header missing" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_format_returns_401(self):
        from api.deps import get_current_user

        mock_request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization="InvalidToken")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authorization header format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_without_bearer_prefix_returns_401(self):
        from api.deps import get_current_user

        mock_request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization="SomeToken")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authorization header format" in exc_info.value.detail
