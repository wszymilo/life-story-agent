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


def test_get_prompt_hash():
    """Test prompt hash generation."""
    import services.evaluation as eval_module

    result = eval_module.get_prompt_hash("test prompt")
    assert len(result) == 16
    assert eval_module.get_prompt_hash("test prompt") == eval_module.get_prompt_hash("test prompt")
    assert eval_module.get_prompt_hash("different") != eval_module.get_prompt_hash("test prompt")