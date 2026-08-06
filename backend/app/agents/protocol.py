"""Typed protocol shared by all agents in a StudyMummy run."""

from enum import StrEnum
from typing import Literal

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field


class AgentIntent(StrEnum):
    REQUEST_HINT = "request_hint"
    EXPLAIN_CONCEPT = "explain_concept"
    EVALUATE_ANSWER = "evaluate_answer"
    SOLVE_TASK = "solve_task"
    PLAN_LEARNING = "plan_learning"
    SCHEDULE_EVENT = "schedule_event"
    GENERAL_QUESTION = "general_question"


class AgentAction(StrEnum):
    ASK_SOCRATIC_QUESTION = "ask_socratic_question"
    GIVE_HINT = "give_hint"
    EXPLAIN = "explain"
    EVALUATE = "evaluate"
    CREATE_PLAN = "create_plan"
    SCHEDULE = "schedule"
    CLARIFY = "clarify"


class AgentContext(BaseModel):
    user_id: str
    session_id: str
    message: str
    help_level: int = Field(default=1, ge=1, le=4)
    current_task_id: str | None = None
    document_id: str | None = None
    task_context: str | None = None
    extra_context: str | None = None
    rag_context: str | None = None
    history: list[ChatCompletionMessageParam] = Field(default_factory=list)
    current_time: str


class AgentPlan(BaseModel):
    intent: AgentIntent
    action: AgentAction
    objective: str
    decision_basis: str
    tool_names: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class AgentReview(BaseModel):
    approved: bool
    feedback: str = ""
    revised_response: str | None = None


class AgentStep(BaseModel):
    agent: Literal["perception", "planner", "tutor", "reviewer", "memory"]
    phase: Literal["perceive", "plan", "act", "review", "remember"]
    summary: str
    duration_ms: float = 0.0


class AgentRunResult(BaseModel):
    response: str
    plan: AgentPlan
    tool_calls: list[str] = Field(default_factory=list)
    steps: list[AgentStep] = Field(default_factory=list)
    reviewed: bool = False

    @property
    def agents_involved(self) -> list[str]:
        return list(dict.fromkeys(step.agent for step in self.steps))
