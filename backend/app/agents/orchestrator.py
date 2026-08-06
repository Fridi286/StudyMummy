"""Observable multi-agent workflow for one tutoring turn."""

import time

from app.agents.planner import PlanningAgent
from app.agents.protocol import AgentContext, AgentRunResult, AgentStep
from app.agents.reviewer import ReviewerAgent
from app.agents.tutor import TutorAgent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.llm_service import LLMService

log = get_logger(__name__)


class AgentOrchestrator:
    """Coordinates specialized agents while keeping all side effects tool-scoped."""

    def __init__(self, llm: LLMService | None = None):
        shared_llm = llm or LLMService()
        self.planner = PlanningAgent(shared_llm)
        self.tutor = TutorAgent(shared_llm)
        self.reviewer = ReviewerAgent(shared_llm)
        self.settings = get_settings()

    async def run(self, context: AgentContext) -> AgentRunResult:
        steps: list[AgentStep] = [
            AgentStep(
                agent="perception",
                phase="perceive",
                summary=(
                    f"Eingabe normalisiert; Aufgabe={'vorhanden' if context.current_task_id else 'nicht gesetzt'}; "
                    f"Aufgabenkontext={'geladen' if context.task_context else 'nicht geladen'}; "
                    f"RAG-Kontext={'vorhanden' if context.rag_context else 'nicht vorhanden'}."
                ),
            )
        ]

        started = time.perf_counter()
        plan = await self.planner.plan(context)
        steps.append(AgentStep(
            agent="planner",
            phase="plan",
            summary=f"{plan.action.value}: {plan.objective}",
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        ))

        started = time.perf_counter()
        draft, tool_calls = await self.tutor.act(context, plan)
        steps.append(AgentStep(
            agent="tutor",
            phase="act",
            summary=f"Plan ausgeführt; {len(tool_calls)} Tool-Aufruf(e).",
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        ))

        reviewed = False
        response = draft
        if self.settings.agent_review_enabled:
            started = time.perf_counter()
            review = await self.reviewer.review(context, plan, draft)
            reviewed = True
            if not review.approved and review.revised_response:
                response = review.revised_response
            steps.append(AgentStep(
                agent="reviewer",
                phase="review",
                summary="Freigegeben." if review.approved else f"Überarbeitet: {review.feedback}",
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
            ))

        log.info(
            "Agent run completed: action=%s agents=%s tools=%s reviewed=%s",
            plan.action,
            [step.agent for step in steps],
            tool_calls,
            reviewed,
        )
        return AgentRunResult(
            response=response,
            plan=plan,
            tool_calls=tool_calls,
            steps=steps,
            reviewed=reviewed,
        )
