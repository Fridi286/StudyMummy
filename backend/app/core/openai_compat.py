"""Compatibility helpers for model-specific OpenAI request parameters."""


_DEFAULT_TEMPERATURE_MODEL_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def temperature_kwargs(model: str, temperature: float) -> dict[str, float]:
    """Return a temperature parameter only when the selected model supports it.

    Reasoning-model families reject non-default temperature values. Omitting the
    parameter lets the provider apply its supported default instead of turning a
    recoverable agent step into an HTTP 400 response.
    """
    normalized_model = model.strip().casefold()
    if normalized_model.startswith(_DEFAULT_TEMPERATURE_MODEL_PREFIXES):
        return {}
    return {"temperature": temperature}


def tool_calling_kwargs(model: str) -> dict[str, str]:
    """Return compatibility parameters for Chat Completions tool calls.

    Current GPT-5 reasoning variants reject function tools on the Chat
    Completions endpoint while their default reasoning effort is active.  The
    provider explicitly supports the same request with reasoning disabled.
    """
    normalized_model = model.strip().casefold()
    if normalized_model.startswith("gpt-5"):
        return {"reasoning_effort": "none"}
    return {}
