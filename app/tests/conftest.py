import pytest

from config import get_settings


@pytest.fixture(autouse=True)
def _set_openai_api_key_for_tests(monkeypatch):
    """Guarantee a non-empty OpenAI API key for unit tests.

    Service guards (e.g. generate_meta_story, generate_summary) raise
    ValueError when settings.openai_api_key is empty. Unit tests either mock
    the OpenAI client or use fake services and never make real API calls, so a
    dummy key lets them pass the guard without depending on CI secrets or a
    local .env. monkeypatch restores the original value after each test.
    """
    monkeypatch.setattr(get_settings(), "openai_api_key", "test-key")
