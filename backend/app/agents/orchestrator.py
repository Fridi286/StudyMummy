"""Message-driven hierarchical multi-agent workflow for one tutoring turn."""

import time

from app.agents.planner import PlanningAgent
from app.agents.protocol import (
    AgentContext,
    AgentId,
    AgentMessage,
    AgentRunResult,
    AgentStep,
    MessageEndpoint,
    MessageKind,
    MessagePerformative,
    ToolStatus,
)
from app.agents.reviewer import ReviewerAgent
from app.agents.runtime import AgentBlackboard, MASAgent, MASMessageBus
from app.agents.tutor import TutorAgent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.llm_service import LLMService

log = get_logger(__name__)


class AgentOrchestrator:
    """Dispatch messages without deciding specialist content on the agents' behalf."""

    def __init__(self, llm: LLMService | None = None):
        shared_llm = llm or LLMService()
        self.planner = PlanningAgent(shared_llm)
        self.tutor = TutorAgent(shared_llm)
        self.reviewer = ReviewerAgent(shared_llm)
        self.agents: dict[AgentId, MASAgent] = {
            AgentId.PLANNER: self.planner,
            AgentId.TUTOR: self.tutor,
            AgentId.REVIEWER: self.reviewer,
        }
        self.settings = get_settings()

    async def run(self, context: AgentContext) -> AgentRunResult:
        states = {
            agent_id: agent.create_state()
            for agent_id, agent in self.agents.items()
        }
        bus = MASMessageBus(states)
        blackboard = AgentBlackboard(
            context=context,
            max_rounds=self.settings.agent_max_coordination_rounds,
            review_enabled=self.settings.agent_review_enabled,
        )
        steps: list[AgentStep] = [
            AgentStep(
                agent="environment",
                phase="perceive",
                summary=(
                    f"Eingabe normalisiert; Aufgabe={'vorhanden' if context.current_task_id else 'nicht gesetzt'}; "
                    f"Aufgabenkontext={'geladen' if context.task_context else 'nicht geladen'}; "
                    f"RAG-Kontext={'vorhanden' if context.rag_context else 'nicht vorhanden'}."
                ),
            )
        ]
        bus.publish(
            AgentMessage(
                sender=MessageEndpoint.USER,
                recipient=MessageEndpoint.PLANNER,
                performative=MessagePerformative.REQUEST,
                kind=MessageKind.PLAN_REQUEST,
                summary="Nutzerziel zur Planung an den Planner übergeben.",
                payload={"message": context.message},
            )
        )

        max_dispatches = self.settings.agent_max_coordination_rounds * 4 + 2
        dispatches = 0
        while dispatches < max_dispatches:
            message = bus.receive()
            if message is None:
                break
            dispatches += 1

            if message.recipient == MessageEndpoint.COORDINATOR:
                blackboard.final_response = str(message.payload.get("response", "")).strip()
                steps.append(
                    AgentStep(
                        agent="coordinator",
                        phase="coordinate",
                        summary=message.summary,
                        round=message.round,
                        message_id=message.message_id,
                    )
                )
                break

            agent_id = AgentId(message.recipient.value)
            agent = self.agents[agent_id]
            state = states[agent_id]
            started = time.perf_counter()
            outgoing = await agent.handle(message, blackboard, state)
            state.decisions_made += 1
            state.last_decision = outgoing[0].summary if outgoing else "Keine Folgebotschaft erzeugt."
            steps.append(
                AgentStep(
                    agent=agent_id.value,
                    phase=self._phase_for(message.kind),
                    summary=state.last_decision,
                    duration_ms=round((time.perf_counter() - started) * 1000, 1),
                    round=message.round,
                    message_id=message.message_id,
                )
            )
            for outgoing_message in outgoing:
                bus.publish(outgoing_message)

        if not blackboard.final_response:
            blackboard.final_response = blackboard.draft.strip() or (
                "Ich konnte den Agentenlauf nicht zuverlässig abschließen. "
                "Welchen Schritt hast du zuletzt versucht?"
            )
            steps.append(
                AgentStep(
                    agent="coordinator",
                    phase="coordinate",
                    summary="Sicherer Laufzeit-Fallback nach leerer Nachrichtenwarteschlange.",
                    round=blackboard.current_round,
                )
            )
        if blackboard.plan is None:
            raise RuntimeError("MAS run finished without a plan")

        successful_tools = [
            observation.tool_name
            for observation in blackboard.observations
            if observation.status == ToolStatus.SUCCEEDED
        ]
        reviewed = states[AgentId.REVIEWER].decisions_made > 0
        log.info(
            "MAS run completed: action=%s agents=%s tools=%s reviewed=%s rounds=%s messages=%s",
            blackboard.plan.action,
            [state.agent.value for state in states.values() if state.decisions_made],
            successful_tools,
            reviewed,
            blackboard.current_round,
            len(bus.communications),
        )
        return AgentRunResult(
            response=blackboard.final_response,
            plan=blackboard.plan,
            tool_calls=successful_tools,
            tool_observations=blackboard.observations,
            steps=steps,
            communications=bus.communications,
            agent_states=list(states.values()),
            coordination_rounds=blackboard.current_round,
            reviewed=reviewed,
        )

    @staticmethod
    def _phase_for(kind: MessageKind):
        return {
            MessageKind.PLAN_REQUEST: "plan",
            MessageKind.REPLAN_REQUEST: "replan",
            MessageKind.EXECUTE_PLAN: "act",
            MessageKind.REVISION_REQUEST: "revise",
            MessageKind.REVIEW_REQUEST: "review",
        }[kind]
