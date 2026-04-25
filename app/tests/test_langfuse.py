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


def test_start_trace_without_client():
    """Test start_trace returns None when no client."""
    with patch("api.langfuse_config._langfuse_client", None):
        from api.langfuse_config import start_trace

        result = start_trace("story_session", user_id="user123")
        assert result is None


def test_start_trace_with_client():
    """Test start_trace creates a trace."""
    mock_client = MagicMock()
    mock_trace = MagicMock()
    mock_trace.id = "trace-abc-123"
    mock_client.trace.return_value = mock_trace

    with patch("api.langfuse_config._langfuse_client", mock_client):
        from api.langfuse_config import start_trace

        result = start_trace("story_session", user_id="user123", metadata={"foo": "bar"})
        assert result == "trace-abc-123"
        mock_client.trace.assert_called_once()


def test_log_generation_without_client():
    """Test log_generation returns early without client."""
    with patch("api.langfuse_config._langfuse_client", None):
        from api.langfuse_config import log_generation

        # Should not raise
        log_generation("prompt", "completion", "gpt-4o-mini")


def test_log_generation_with_client():
    """Test log_generation with client."""
    mock_client = MagicMock()

    with patch("api.langfuse_config._langfuse_client", mock_client):
        with patch("api.langfuse_config.trace_ctx", MagicMock(return_value="trace-123")):
            from api.langfuse_config import log_generation

            log_generation(
                prompt="prompt",
                completion="completion",
                model="gpt-4o-mini",
                usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                metadata={"operation": "test"},
            )
            assert mock_client.generation.called


def test_log_score():
    """Test log_score attaches a score to a trace."""
    mock_client = MagicMock()

    with patch("api.langfuse_config._langfuse_client", mock_client):
        from api.langfuse_config import log_score

        log_score("trace-123", "factual_accuracy", 0.95, "Great summary")
        mock_client.score.assert_called_once_with(
            trace_id="trace-123",
            name="factual_accuracy",
            value=0.95,
            comment="Great summary",
        )


def test_update_trace():
    """Test update_trace updates trace metadata."""
    mock_client = MagicMock()

    with patch("api.langfuse_config._langfuse_client", mock_client):
        from api.langfuse_config import update_trace

        update_trace("trace-123", metadata={"status": "complete"}, status="complete")
        mock_client.trace.assert_called_once_with(
            id="trace-123",
            metadata={"status": "complete"},
        )


def test_compute_cost_gpt4o_mini():
    """Test cost computation for GPT-4o-mini."""
    from api.langfuse_config import _compute_cost

    usage = {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}
    cost = _compute_cost("gpt-4o-mini", usage)
    # (1000/1M * 0.15) + (500/1M * 0.60) = 0.00015 + 0.0003 = 0.00045
    assert cost == 0.00045


def test_compute_cost_whisper():
    """Test cost computation for Whisper."""
    from api.langfuse_config import _compute_cost

    usage = {"duration_minutes": 5.0}
    cost = _compute_cost("whisper-1", usage)
    # 5.0 * 0.006 = 0.03
    assert cost == 0.03


def test_compute_cost_tts():
    """Test cost computation for TTS."""
    from api.langfuse_config import _compute_cost

    usage = {"characters": 2000}
    cost = _compute_cost("gpt-4o-mini-tts", usage)
    # (2000/1000) * 0.015 = 0.03
    assert cost == 0.03


def test_trace_context():
    """Test trace context get/set."""
    from api.langfuse_config import get_trace_context, set_trace_context

    set_trace_context("trace-456")
    assert get_trace_context() == "trace-456"

    set_trace_context(None)
    assert get_trace_context() is None
