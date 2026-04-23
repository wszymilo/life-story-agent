def raise_openai_error(error: Exception, operation: str) -> None:
    """Classify an OpenAI API error and raise a user-friendly RuntimeError.

    Checks for common OpenAI error patterns (invalid API key, rate limit,
    max tokens exceeded) and raises with a clear message prefixed by the
    operation name.

    Args:
        error: The original exception from the OpenAI client.
        operation: Human-readable operation name (e.g., "Transcription").

    Raises:
        RuntimeError: Always raised with a classified message.
    """
    err_msg = str(error)
    err_msg_lower = err_msg.lower()

    if "incorrect api key" in err_msg_lower or "invalid_api_key" in err_msg_lower:
        raise RuntimeError(f"{operation} failed: Invalid API key")
    if "api_key" in err_msg_lower:
        raise RuntimeError(f"{operation} failed: API key issue")
    if "rate_limit" in err_msg_lower:
        raise RuntimeError(f"{operation} failed: Rate limit exceeded")
    if "max_tokens" in err_msg_lower:
        raise RuntimeError(f"{operation} failed: Text too long (max 4096 characters)")
    raise RuntimeError(f"{operation} failed: {err_msg}")
