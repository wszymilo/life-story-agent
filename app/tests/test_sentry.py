"""Tests for Sentry configuration."""

from unittest.mock import patch


def test_init_sentry_without_dsn():
    """Test Sentry init is skipped when no DSN configured."""
    with patch("api.sentry_config.get_settings") as mock_settings:
        mock_settings.return_value.sentry_dsn = ""
        mock_settings.return_value.environment = "test"

        from api.sentry_config import init_sentry

        init_sentry()


def test_init_sentry_with_dsn():
    """Test Sentry init when DSN is configured."""
    with patch("api.sentry_config.get_settings") as mock_settings:
        mock_settings.return_value.sentry_dsn = "https://test@test.sentry.io/123"
        mock_settings.return_value.environment = "test"

        with patch("api.sentry_config.sentry_sdk") as mock_sentry:
            from api.sentry_config import init_sentry

            init_sentry()
            mock_sentry.init.assert_called_once()


def test_capture_exception():
    """Test exception capture."""
    with patch("api.sentry_config.sentry_sdk") as mock_sentry:
        from api.sentry_config import capture_exception

        exc = ValueError("test error")
        capture_exception(exc, extra="test")
        mock_sentry.capture_exception.assert_called_once_with(exc)


def test_set_user_context():
    """Test user context setting."""
    with patch("api.sentry_config.sentry_sdk") as mock_sentry:
        from api.sentry_config import set_user_context

        set_user_context("user123", "test@example.com")
        mock_sentry.set_user.assert_called_once_with(
            {"id": "user123", "email": "test@example.com"}
        )


def test_add_breadcrumb():
    """Test breadcrumb addition."""
    with patch("api.sentry_config.sentry_sdk") as mock_sentry:
        from api.sentry_config import add_breadcrumb

        add_breadcrumb("test message", category="test", key="value")
        mock_sentry.add_breadcrumb.assert_called_once_with(
            message="test message",
            category="test",
            data={"key": "value"},
        )