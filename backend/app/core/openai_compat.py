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
