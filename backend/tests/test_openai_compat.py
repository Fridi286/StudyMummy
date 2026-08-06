import pytest

from app.core.openai_compat import temperature_kwargs


@pytest.mark.parametrize("model", ["gpt-5", "gpt-5.6-luna", "o1", "o3-mini", "o4-mini"])
def test_temperature_is_omitted_for_default_only_models(model: str):
    assert temperature_kwargs(model, 0.3) == {}


@pytest.mark.parametrize("model", ["gpt-4o", "gpt-4o-mini", "qwen2.5"])
def test_temperature_is_preserved_for_supported_models(model: str):
    assert temperature_kwargs(model, 0.3) == {"temperature": 0.3}
