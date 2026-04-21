"""Fake LLM Service - programmable responses for testing without real API calls."""

from typing import Any
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    """Fake LLM response object."""
    content: str
    tokens_used: int = 0
    model: str = "gpt-5-nano"


class FakeLLMService:
    """A fake LLM service with programmable response behavior."""

    def __init__(self):
        self._responses: dict[str, str] = {}
        self._default_response = "To jest testowa odpowiedź LLM."
        self._calls: list[dict[str, Any]] = []

    def program_response(self, prompt_contains: str, response: str) -> "FakeLLMService":
        """Set a response for prompts containing specific text.
        
        Args:
            prompt_contains: Substring to match in prompt
            response: Response to return when prompt matches
            
        Returns:
            Self for fluent interface
        """
        self._responses[prompt_contains.lower()] = response
        return self

    def set_default_response(self, response: str) -> None:
        """Set the default response when no programmed response matches."""
        self._default_response = response

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a completion for the given prompt.
        
        Returns matching programmed response or default.
        """
        prompt_lower = prompt.lower()
        self._calls.append({
            "prompt": prompt,
            "prompt_length": len(prompt),
            "kwargs": kwargs,
        })

        # Find matching response
        for trigger, response in self._responses.items():
            if trigger in prompt_lower:
                return LLMResponse(
                    content=response,
                    tokens_used=len(response),
                )

        return LLMResponse(
            content=self._default_response,
            tokens_used=len(self._default_response),
        )

    def get_calls(self) -> list[dict[str, Any]]:
        """Get list of calls made to this service."""
        return self._calls

    def assert_prompt_contains(self, text: str) -> None:
        """Assert that a prompt contained specific text."""
        prompts = [call["prompt"] for call in self._calls]
        text_lower = text.lower()
        assert any(text_lower in p.lower() for p in prompts), \
            f"Expected prompt to contain '{text}', got {prompts}"

    def assert_called(self) -> None:
        """Assert that service was called at least once."""
        assert len(self._calls) > 0, "LLM was not called"

    def reset(self) -> None:
        """Reset call history and responses."""
        self._calls = []
        self._responses = {}
