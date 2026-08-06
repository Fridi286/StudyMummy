from typing import Any, cast

import pytest

from app.agents.orchestrator import AgentOrchestrator
from app.agents.planner import PlanningAgent
from app.agents.protocol import AgentAction, AgentContext, AgentIntent
from app.services.llm_service import LLMService


class FakeAgentLLM:
    def __init__(self, structured: list[dict[str, Any] | None], draft: str = "Was wäre dein erster Schritt?"):
        self.structured = list(structured)
        self.draft = draft
        self.allowed_tools: list[str] = []

    async def complete_json(self, **_kwargs: Any) -> dict[str, Any] | None:
        return self.structured.pop(0) if self.structured else None

    async def chat_with_tools(self, **kwargs: Any) -> tuple[str, list[str]]:
        self.allowed_tools = list(kwargs.get("allowed_tool_names") or [])
        return self.draft, []


def context(message: str = "Ich brauche einen Hinweis.") -> AgentContext:
    return AgentContext(
        user_id="user_1",
        session_id="session_1",
        message=message,
        help_level=1,
        current_task_id="task_1",
        history=[{"role": "user", "content": message}],
        current_time="2026-08-02T12:00:00+00:00",
    )


@pytest.mark.asyncio
async def test_planner_enforces_capability_policy():
    llm = FakeAgentLLM(structured=[{
        "intent": "evaluate_answer",
        "action": "evaluate",
        "objective": "Antwort prüfen",
        "decision_basis": "Eine Antwort liegt vor",
        "tool_names": ["evaluate_answer", "add_calendar_note", "unknown_tool"],
        "success_criteria": ["Bewertung ist nachvollziehbar"],
    }])
    planner = PlanningAgent(cast(LLMService, cast(object, llm)))

    plan = await planner.plan(context("Meine Antwort ist 4."))

    assert plan.intent == AgentIntent.EVALUATE_ANSWER
    assert plan.action == AgentAction.EVALUATE
    assert plan.tool_names == ["evaluate_answer"]


@pytest.mark.asyncio
async def test_orchestrator_runs_specialists_and_returns_trace():
    llm = FakeAgentLLM(structured=[None, {"approved": True, "feedback": "Passt."}])
    orchestrator = AgentOrchestrator(cast(LLMService, cast(object, llm)))

    result = await orchestrator.run(context())

    assert result.response == "Was wäre dein erster Schritt?"
    assert result.plan.action == AgentAction.GIVE_HINT
    assert result.reviewed is True
    assert result.agents_involved == ["perception", "planner", "tutor", "reviewer"]
    assert llm.allowed_tools == ["evaluate_answer"]


@pytest.mark.asyncio
async def test_reviewer_can_replace_unsafe_draft():
    llm = FakeAgentLLM(
        structured=[
            None,
            {
                "approved": False,
                "feedback": "Die Antwort verrät zu viel.",
                "revised_response": "Welchen Zusammenhang erkennst du zwischen den beiden Größen?",
            },
        ],
        draft="Hier ist sofort die vollständige Lösung.",
    )
    orchestrator = AgentOrchestrator(cast(LLMService, cast(object, llm)))

    result = await orchestrator.run(context())

    assert result.response.startswith("Welchen Zusammenhang")
    assert result.steps[-1].agent == "reviewer"
    assert "Überarbeitet" in result.steps[-1].summary
