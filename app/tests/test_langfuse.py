"""Tests for LangFuse configuration."""

from unittest.mock import MagicMock, patch


def test_init_langfuse_without_keys():
    """Test LangFuse init is skipped when no keys configured."""
    mock_settings = MagicMock()
    mock_settings.langfuse_public_key = ""
    mock_settings.langfuse_secret_key = ""

    with patch("api.langfuse_config.settings", mock_settings):
        with patch("api.langfuse_config._langfuse_client", None):
            from api.langfuse_config import init_langfuse

            result = init_langfuse()
            assert result is None


def test_init_langfuse_with_keys():
    """Test LangFuse init when keys are configured."""
    mock_settings = MagicMock()
    mock_settings.langfuse_public_key = "pk-public"
    mock_settings.langfuse_secret_key = "sk-secret"
    mock_settings.langfuse_base_url = "https://cloud.langfuse.com"

    with patch("api.langfuse_config.settings", mock_settings):
        with patch("api.langfuse_config.Langfuse") as mock_langfuse:
            mock_instance = MagicMock()
            mock_langfuse.return_value = mock_instance
            from api.langfuse_config import init_langfuse

            result = init_langfuse()
            mock_langfuse.assert_called_once()
            assert result == mock_instance


def test_log_generation_returns_early_without_client():
    """Test log_generation returns early without client."""
    from api.langfuse_config import log_generation

    log_generation("prompt", "completion", "gpt-4o-mini")


def test_log_generation_with_client():
    """Test log_generation with client."""
    mock_context_manager = MagicMock()
    mock_client = MagicMock()
    mock_client.start_as_current_observation.return_value = mock_context_manager

    with patch("api.langfuse_config._langfuse_client", mock_client):
        from api.langfuse_config import log_generation

        log_generation("prompt", "completion", "gpt-4o-mini", user_id="user123")
        assert mock_client.start_as_current_observation.called


