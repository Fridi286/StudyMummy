from types import SimpleNamespace
from typing import cast

import pytest
from openai import AsyncOpenAI

from app.agents.protocol import ToolStatus
from app.services.llm_service import LLMService


class FakeMessage:
    def __init__(self, content: str | None = "", tool_calls: list[object] | None = None):
        self.content: str | None = content
        self.tool_calls: list[object] | None = tool_calls

    def model_dump(self, **_kwargs: object):
        result: dict[str, object] = {"role": "assistant"}
        if self.content is not None:
            result["content"] = self.content
        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls
        return result


class FakeCompletions:
    def __init__(self, responses: list[FakeMessage] | None = None, error: Exception | None = None):
        self.responses: list[FakeMessage] = list(responses or [])
        self.error: Exception | None = error
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs: object):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        message = self.responses.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClient:
    def __init__(self, completions: FakeCompletions):
        self.chat: SimpleNamespace = SimpleNamespace(completions=completions)


@pytest.mark.asyncio
async def test_chat_with_tools_returns_fallback_on_api_error():
    service = LLMService()
    service.client = cast(AsyncOpenAI, cast(object, FakeClient(FakeCompletions(error=RuntimeError("timeout")))))

    result = await service.chat_with_tools(
        messages=[{"role": "user", "content": "Ich brauche Hilfe."}]
    )

    assert "keine zuverlässige" in result.response
    assert result.observations == []


@pytest.mark.asyncio
async def test_chat_with_tools_handles_invalid_tool_arguments_semantically():
    invalid_tool_call = SimpleNamespace(
        id="call_1",
        type="function",
        function=SimpleNamespace(
            name="evaluate_answer",
            arguments="{not-json",
        ),
    )
    service = LLMService()
    service.client = cast(AsyncOpenAI, cast(object, FakeClient(
        FakeCompletions(
            responses=[
                FakeMessage(content=None, tool_calls=[invalid_tool_call]),
                FakeMessage(content="Ich konnte die Tool-Eingabe nicht auswerten. Was hast du versucht?"),
            ]
        )
    )))

    result = await service.chat_with_tools(
        messages=[{"role": "user", "content": "Meine Antwort ist 2."}]
    )

    assert "Tool-Eingabe" in result.response
    assert "?" in result.response
    assert result.successful_tool_names == []
    assert result.observations[0].tool_name == "evaluate_answer"
    assert result.observations[0].status == ToolStatus.INVALID_ARGUMENTS


@pytest.mark.asyncio
async def test_extract_tasks_from_text_returns_empty_list_on_invalid_json():
    service = LLMService()
    service.client = cast(AsyncOpenAI, cast(object, FakeClient(
        FakeCompletions(responses=[FakeMessage(content="{not-json")])
    )))

    tasks = await service.extract_tasks_from_text("Aufgabe 1: Berechne 2+2.")

    assert tasks == []


@pytest.mark.asyncio
async def test_gpt5_chat_tool_call_disables_reasoning_effort():
    completions = FakeCompletions(responses=[FakeMessage(content="Welchen Schritt versuchst du?")])
    service = LLMService()
    service.model = "gpt-5.6-luna"
    service.client = cast(AsyncOpenAI, cast(object, FakeClient(completions)))

    await service.chat_with_tools(
        messages=[{"role": "user", "content": "Gib mir einen Hinweis."}],
        allowed_tool_names=["evaluate_answer"],
    )

    assert completions.calls[0]["reasoning_effort"] == "none"
    assert completions.calls[0]["tool_choice"] == "auto"
