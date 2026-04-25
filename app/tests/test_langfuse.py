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
    """Test start_trace creates a trace via legacy ingestion API."""
    mock_client = MagicMock()
    mock_client.create_trace_id.side_effect = [
        "trace-abc-123",
        "event-id-456",
    ]
    mock_client.api.ingestion.batch.return_value = MagicMock(
        successes=[MagicMock(status=201)], errors=[]
    )

    with patch("api.langfuse_config._langfuse_client", mock_client):
        from api.langfuse_config import start_trace

        result = start_trace(
            "story_session",
            user_id="user123",
            session_id="session456",
            metadata={"foo": "bar"},
        )
        assert result == "trace-abc-123"
        mock_client.create_trace_id.assert_called()
        mock_client.api.ingestion.batch.assert_called_once()
        call_args = mock_client.api.ingestion.batch.call_args
        batch = call_args.kwargs["batch"]
        assert len(batch) == 1
        assert batch[0].body.id == "trace-abc-123"
        assert batch[0].body.name == "story_session"
        assert batch[0].body.user_id == "user123"
        assert batch[0].body.session_id == "session456"


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


def test_update_trace_is_noop_in_v4():
    """Test update_trace is a no-op in LangFuse v4 SDK."""
    mock_client = MagicMock()

    with patch("api.langfuse_config._langfuse_client", mock_client):
        from api.langfuse_config import update_trace

        update_trace("trace-123", metadata={"status": "complete"}, status="complete")
        # In v4, trace update is not supported via legacy API; should be a no-op
        mock_client.api.ingestion.batch.assert_not_called()
