"""Planning agent: turns perceived state into one bounded next action."""

from typing import Any

from app.agents.protocol import (
    AgentAction,
    AgentContext,
    AgentId,
    AgentIntent,
    AgentLocalState,
    AgentMessage,
    AgentPlan,
    MessageEndpoint,
    MessageKind,
    MessagePerformative,
    ToolObservation,
)
from app.agents.runtime import AgentBlackboard, MASAgent
from app.core.logging import get_logger
from app.services.llm_service import LLMService

log = get_logger(__name__)

SAFE_TOOL_POLICY: dict[AgentAction, set[str]] = {
    AgentAction.ASK_SOCRATIC_QUESTION: {"evaluate_answer"},
    AgentAction.GIVE_HINT: {"evaluate_answer"},
    AgentAction.EXPLAIN: {"evaluate_answer"},
    AgentAction.EVALUATE: {"evaluate_answer", "update_learning_profile", "award_coins_and_exp"},
    AgentAction.CREATE_PLAN: set(),
    AgentAction.SCHEDULE: {"add_calendar_note"},
    AgentAction.CLARIFY: set(),
}

PLANNER_PROMPT = """Du bist der Planning Agent von StudyMummy.
Analysiere den aktuellen Lernzustand und plane exakt die naechste sinnvolle Aktion.
Wenn Koordinationsfeedback, ein vorheriger Plan oder Toolbeobachtungen vorliegen,
pruefe sie und ersetze einen ungeeigneten Plan gezielt.
Du antwortest ausschliesslich als JSON mit diesen Feldern:
- intent: request_hint, explain_concept, evaluate_answer, solve_task, plan_learning, schedule_event oder general_question
- action: ask_socratic_question, give_hint, explain, evaluate, create_plan, schedule oder clarify
- objective: ein kurzer, beobachtbarer Zweck
- decision_basis: kurze fachliche Entscheidungsgrundlage, keine interne Gedankenkette
- tool_names: nur evaluate_answer, update_learning_profile, award_coins_and_exp oder add_calendar_note
- success_criteria: 1 bis 3 pruefbare Kriterien

Plane nur einen Schritt. Verrate bei niedriger Hilfestufe keine vollstaendige Loesung.
Tools sind Vorschlaege; eine Policy reduziert die Rechte anschliessend nochmals.
"""


class PlanningAgent(MASAgent):
    name = "planner"
    agent_id = AgentId.PLANNER
    objective = "Aus dem Lernzustand einen begrenzten, überprüfbaren nächsten Schritt ableiten."
    capabilities = ("intent_classification", "action_selection", "tool_scoping", "replanning")

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def plan(
        self,
        context: AgentContext,
        *,
        feedback: str = "",
        previous_plan: AgentPlan | None = None,
        observations: list[ToolObservation] | None = None,
    ) -> AgentPlan:
        payload = {
            "message": context.message,
            "help_level": context.help_level,
            "current_task_id": context.current_task_id,
            "task_context": context.task_context,
            "has_document_context": bool(context.rag_context or context.extra_context or context.task_context),
            "coordination_feedback": feedback or None,
            "previous_plan": previous_plan.model_dump(mode="json") if previous_plan else None,
            "tool_observations": [
                observation.model_dump(mode="json")
                for observation in (observations or [])
            ],
        }
        raw = await self.llm.complete_json(
            system_prompt=PLANNER_PROMPT,
            payload=payload,
            temperature=0.0,
        )
        plan = self._parse_plan(raw) or self._fallback_plan(context)
        allowed = SAFE_TOOL_POLICY[plan.action]
        plan.tool_names = [name for name in plan.tool_names if name in allowed]
        if plan.action in {AgentAction.ASK_SOCRATIC_QUESTION, AgentAction.GIVE_HINT, AgentAction.EXPLAIN}:
            if context.current_task_id and "evaluate_answer" not in plan.tool_names:
                plan.tool_names.append("evaluate_answer")
        log.info(
            "Planning completed: intent=%s action=%s tools=%s",
            plan.intent,
            plan.action,
            plan.tool_names,
        )
        return plan

    async def handle(
        self,
        message: AgentMessage,
        blackboard: AgentBlackboard,
        state: AgentLocalState,
    ) -> list[AgentMessage]:
        if message.kind not in {MessageKind.PLAN_REQUEST, MessageKind.REPLAN_REQUEST}:
            raise ValueError(f"Planner cannot handle message kind {message.kind}")

        is_replan = message.kind == MessageKind.REPLAN_REQUEST
        previous_plan = blackboard.plan if is_replan else None
        plan = await self.plan(
            blackboard.context,
            feedback=str(message.payload.get("feedback", "")),
            previous_plan=previous_plan,
            observations=blackboard.observations,
        )
        blackboard.plan = plan
        state.local_memory = {
            "last_intent": plan.intent.value,
            "last_action": plan.action.value,
            "last_objective": plan.objective,
        }
        verb = "neu geplant" if is_replan else "geplant"
        return [
            AgentMessage(
                sender=MessageEndpoint.PLANNER,
                recipient=MessageEndpoint.TUTOR,
                performative=MessagePerformative.DELEGATE,
                kind=MessageKind.EXECUTE_PLAN,
                round=blackboard.current_round,
                summary=f"Aktion {plan.action.value} {verb} und an Tutor delegiert.",
                payload={"plan": plan},
            )
        ]

    @staticmethod
    def _parse_plan(raw: dict[str, Any] | None) -> AgentPlan | None:
        if not raw:
            return None
        try:
            return AgentPlan.model_validate(raw)
        except Exception as exc:
            log.warning("Planner returned invalid structure, using fallback: %s", exc)
            return None

    @staticmethod
    def _fallback_plan(context: AgentContext) -> AgentPlan:
        text = context.message.casefold()
        if any(word in text for word in ("termin", "deadline", "pruefung", "prüfung", "kalender")):
            return AgentPlan(
                intent=AgentIntent.SCHEDULE_EVENT,
                action=AgentAction.SCHEDULE,
                objective="Den genannten Lerntermin eindeutig erfassen oder fehlende Angaben erfragen.",
                decision_basis="Die Nachricht enthält einen erkennbaren Terminbezug.",
                tool_names=["add_calendar_note"],
                success_criteria=["Datum und Zweck sind eindeutig", "Termin wird nur nach ausreichenden Angaben angelegt"],
            )
        if any(word in text for word in ("meine antwort", "ist das richtig", "ergebnis", "ich habe")) and context.current_task_id:
            return AgentPlan(
                intent=AgentIntent.EVALUATE_ANSWER,
                action=AgentAction.EVALUATE,
                objective="Die Antwort bewerten und mit einer passenden nächsten Lernfrage fortfahren.",
                decision_basis="Es liegt eine Antwort zu einer aktiven Aufgabe vor.",
                tool_names=["evaluate_answer", "update_learning_profile", "award_coins_and_exp"],
                success_criteria=["Bewertung ist fachlich begründet", "Feedback passt zur Hilfestufe"],
            )
        if any(word in text for word in ("lösung", "loesung", "rechne vor", "schritt für schritt")):
            action = AgentAction.EXPLAIN if context.help_level >= 3 else AgentAction.GIVE_HINT
            return AgentPlan(
                intent=AgentIntent.SOLVE_TASK,
                action=action,
                objective="Beim nächsten Lösungsschritt helfen, ohne unnötig Lernarbeit vorwegzunehmen.",
                decision_basis=f"Der Nutzer fordert konkrete Lösungshilfe auf Hilfestufe {context.help_level} an.",
                tool_names=["evaluate_answer"] if context.current_task_id else [],
                success_criteria=["Nächster Schritt ist verständlich", "Antwort aktiviert den Lernenden"],
            )
        if any(word in text for word in ("hinweis", "tipp", "hilfe", "komme nicht weiter", "verstehe nicht")):
            return AgentPlan(
                intent=AgentIntent.REQUEST_HINT,
                action=AgentAction.GIVE_HINT,
                objective="Einen adaptiven Hinweis geben und Verständnis mit einer Rückfrage prüfen.",
                decision_basis="Die Nachricht signalisiert Unterstützungsbedarf.",
                tool_names=["evaluate_answer"] if context.current_task_id else [],
                success_criteria=["Hinweis entspricht der Hilfestufe", "Eine konkrete Rückfrage folgt"],
            )
        return AgentPlan(
            intent=AgentIntent.GENERAL_QUESTION,
            action=AgentAction.ASK_SOCRATIC_QUESTION,
            objective="Das Lernziel klären und den Lernenden aktiv zum nächsten Gedanken führen.",
            decision_basis="Es gibt noch keine eindeutigere Handlungsabsicht.",
            tool_names=["evaluate_answer"] if context.current_task_id else [],
            success_criteria=["Antwort bezieht sich auf die Frage", "Der nächste Lernschritt ist klar"],
        )
