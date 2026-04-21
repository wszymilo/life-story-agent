"""Tests for rate limiting configuration."""


def test_rate_limiter_configured():
    """Test rate limiter is configured."""
    from api.rate_limit_config import limiter

    assert limiter is not None
    assert hasattr(limiter, "limit")


def test_rate_limit_decorator():
    """Test rate limit decorator can be applied."""
    from api.rate_limit_config import limiter

    @limiter.limit("10/minute")
    def dummy_view(request):
        return {"status": "ok"}

    assert callable(dummy_view)