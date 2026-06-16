"""
Tool-Registry: alle verfügbaren Agent-Tools werden hier zentral registriert.
Neue Tools können einfach hinzugefügt werden, ohne die Agent-Logik zu ändern.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine


ToolFn = Callable[..., Coroutine[Any, Any, Any]]


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]   # JSON Schema
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


def as_openai_tools() -> list[dict[str, Any]]:
    """Gibt alle Tools im OpenAI Function-Calling-Format zurück."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in get_all()
    ]
