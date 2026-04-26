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


def test_log_score():
    """Test log_score attaches a score to a trace via create_score."""
    mock_client = MagicMock()

    with patch("api.langfuse_config._langfuse_client", mock_client):
        from api.langfuse_config import log_score

        log_score("trace-123", "factual_accuracy", 0.95, "Great summary")
        mock_client.create_score.assert_called_once_with(
            trace_id="trace-123",
            name="factual_accuracy",
            value=0.95,
            comment="Great summary",
        )


def test_report_generation_usage_with_usage():
    """Test report_generation_usage calls update_current_generation with usage."""
    mock_client = MagicMock()

    with patch("api.langfuse_config._langfuse_client", mock_client):
        from api.langfuse_config import report_generation_usage

        report_generation_usage(
            "gpt-4o-mini",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_client.update_current_generation.assert_called_once()
        call_kwargs = mock_client.update_current_generation.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["usage_details"] == {
            "input": 100,
            "output": 50,
            "total": 150,
        }


def test_report_generation_usage_without_usage():
    """Test report_generation_usage calls update_current_generation with model only."""
    mock_client = MagicMock()

    with patch("api.langfuse_config._langfuse_client", mock_client):
        from api.langfuse_config import report_generation_usage

        report_generation_usage("whisper-1", usage=None)
        mock_client.update_current_generation.assert_called_once_with(
            model="whisper-1",
        )


def test_report_generation_usage_without_client():
    """Test report_generation_usage returns early when no client."""
    with patch("api.langfuse_config._langfuse_client", None):
        from api.langfuse_config import report_generation_usage

        report_generation_usage("gpt-4o-mini", usage={"prompt_tokens": 10})
        # Should not raise
