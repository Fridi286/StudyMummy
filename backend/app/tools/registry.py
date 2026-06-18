"""
Tool-Registry: alle verfügbaren Agent-Tools werden hier zentral registriert.
Neue Tools können einfach hinzugefügt werden, ohne die Agent-Logik zu ändern.
"""
from dataclasses import dataclass
from typing import Callable, cast
from collections.abc import Coroutine
from typing_extensions import TypedDict
from openai.types.chat import ChatCompletionToolParam

class JSONSchemaProperty(TypedDict, total=False):
    type: str
    description: str
    minimum: int | float
    maximum: int | float
    items: dict[str, str]

class JSONSchema(TypedDict, total=False):
    type: str
    properties: dict[str, JSONSchemaProperty]
    required: list[str]

ToolResult = dict[str, str | int | float | bool | list[str] | list[dict[str, str | list[str]]]] | str
ToolFn = Callable[..., Coroutine[None, None, ToolResult]]


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: JSONSchema   # JSON Schema
    fn: ToolFn


_REGISTRY: dict[str, ToolDefinition] = {}


def register(tool: ToolDefinition) -> ToolDefinition:
    _REGISTRY[tool.name] = tool
    return tool


def get_all() -> list[ToolDefinition]:
    return list(_REGISTRY.values())


def get(name: str) -> ToolDefinition:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown tool: {name!r}")
    return _REGISTRY[name]


def as_openai_tools() -> list[ChatCompletionToolParam]:
    """Gibt alle Tools im OpenAI Function-Calling-Format zurück."""
    tools: list[ChatCompletionToolParam] = []
    for t in get_all():
        tool_param: ChatCompletionToolParam = {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": cast(dict[str, object], cast(object, t.parameters)),
            }
        }
        tools.append(tool_param)
    return tools
