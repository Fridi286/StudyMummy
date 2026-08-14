from types import SimpleNamespace
from typing import cast

import pytest
from openai import AsyncOpenAI

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

    async def create(self, **_kwargs: object):
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

    reply, tool_calls = await service.chat_with_tools(
        messages=[{"role": "user", "content": "Ich brauche Hilfe."}]
    )

    assert "keine zuverlässige" in reply
    assert tool_calls == []


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

    reply, tool_calls = await service.chat_with_tools(
        messages=[{"role": "user", "content": "Meine Antwort ist 2."}]
    )

    assert "Tool-Eingabe" in reply
    assert "?" in reply
    assert tool_calls == []


@pytest.mark.asyncio
async def test_extract_tasks_from_text_returns_empty_list_on_invalid_json():
    service = LLMService()
    service.client = cast(AsyncOpenAI, cast(object, FakeClient(
        FakeCompletions(responses=[FakeMessage(content="{not-json")])
    )))

    tasks = await service.extract_tasks_from_text("Aufgabe 1: Berechne 2+2.")

    assert tasks == []
