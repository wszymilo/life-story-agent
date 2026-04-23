"""Tests for evaluation service."""


def test_should_evaluate_when_disabled():
    """Test evaluation is skipped when disabled."""
    import services.evaluation as eval_module

    original = eval_module.settings.eval_enabled
    eval_module.settings.eval_enabled = False

    try:
        result = eval_module.should_evaluate()
        assert result is False
    finally:
        eval_module.settings.eval_enabled = original
