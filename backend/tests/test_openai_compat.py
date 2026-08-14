import pytest

from app.core.openai_compat import temperature_kwargs, tool_calling_kwargs


@pytest.mark.parametrize("model", ["gpt-5", "gpt-5.6-luna", "o1", "o3-mini", "o4-mini"])
def test_temperature_is_omitted_for_default_only_models(model: str):
    assert temperature_kwargs(model, 0.3) == {}


@pytest.mark.parametrize("model", ["gpt-4o", "gpt-4o-mini", "qwen2.5"])
def test_temperature_is_preserved_for_supported_models(model: str):
    assert temperature_kwargs(model, 0.3) == {"temperature": 0.3}


@pytest.mark.parametrize("model", ["gpt-5", "gpt-5.6-luna", "GPT-5-mini"])
def test_gpt5_tool_calls_disable_reasoning_for_chat_completions(model: str):
    assert tool_calling_kwargs(model) == {"reasoning_effort": "none"}


@pytest.mark.parametrize("model", ["gpt-4o", "o3-mini", "qwen2.5-7b"])
def test_other_tool_calls_do_not_receive_reasoning_override(model: str):
    assert tool_calling_kwargs(model) == {}
