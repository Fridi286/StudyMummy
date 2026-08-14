"""Typed contracts for the StudyMummy multi-agent system."""

from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field, model_validator


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


class AgentId(StrEnum):
    PLANNER = "planner"
    TUTOR = "tutor"
    REVIEWER = "reviewer"


class MessageEndpoint(StrEnum):
    USER = "user"
    PLANNER = "planner"
    TUTOR = "tutor"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"


class MessagePerformative(StrEnum):
    REQUEST = "request"
    DELEGATE = "delegate"
    PROPOSE = "propose"
    CRITIQUE = "critique"
    ACCEPT = "accept"
    INFORM = "inform"


class MessageKind(StrEnum):
    PLAN_REQUEST = "plan_request"
    EXECUTE_PLAN = "execute_plan"
    REVIEW_REQUEST = "review_request"
    REVISION_REQUEST = "revision_request"
    REPLAN_REQUEST = "replan_request"
    FINAL_RESPONSE = "final_response"


class ToolStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    INVALID_ARGUMENTS = "invalid_arguments"


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
    objective: str = Field(min_length=1)
    decision_basis: str = Field(min_length=1)
    tool_names: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(min_length=1, max_length=3)


class ToolObservation(BaseModel):
    tool_name: str
    status: ToolStatus
    result_preview: str = ""


class ToolConversationResult(BaseModel):
    response: str
    observations: list[ToolObservation] = Field(default_factory=list)

    @property
    def successful_tool_names(self) -> list[str]:
        return [
            observation.tool_name
            for observation in self.observations
            if observation.status == ToolStatus.SUCCEEDED
        ]


class TutorResult(BaseModel):
    response: str
    observations: list[ToolObservation] = Field(default_factory=list)


class AgentReview(BaseModel):
    approved: bool
    feedback: str = ""
    requires_replan: bool = False
    revised_response: str | None = None

    @model_validator(mode="after")
    def normalize_approved_review(self) -> "AgentReview":
        if self.approved:
            self.requires_replan = False
            self.revised_response = None
        return self


class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: uuid4().hex)
    sender: MessageEndpoint
    recipient: MessageEndpoint
    performative: MessagePerformative
    kind: MessageKind
    round: int = Field(default=1, ge=1)
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict, exclude=True)


class AgentCommunication(BaseModel):
    message_id: str
    sender: MessageEndpoint
    recipient: MessageEndpoint
    performative: MessagePerformative
    kind: MessageKind
    round: int
    summary: str


class AgentLocalState(BaseModel):
    agent: AgentId
    objective: str
    capabilities: list[str]
    messages_received: int = 0
    messages_sent: int = 0
    decisions_made: int = 0
    last_message_kind: MessageKind | None = None
    last_decision: str = ""
    local_memory: dict[str, str] = Field(default_factory=dict)


class AgentStep(BaseModel):
    agent: Literal["environment", "planner", "tutor", "reviewer", "coordinator", "memory"]
    phase: Literal[
        "perceive",
        "plan",
        "replan",
        "act",
        "revise",
        "review",
        "coordinate",
        "remember",
    ]
    summary: str
    duration_ms: float = 0.0
    round: int = 1
    message_id: str | None = None


class AgentRunResult(BaseModel):
    response: str
    plan: AgentPlan
    tool_calls: list[str] = Field(default_factory=list)
    tool_observations: list[ToolObservation] = Field(default_factory=list)
    steps: list[AgentStep] = Field(default_factory=list)
    communications: list[AgentCommunication] = Field(default_factory=list)
    agent_states: list[AgentLocalState] = Field(default_factory=list)
    coordination_rounds: int = Field(default=1, ge=1)
    reviewed: bool = False

    @property
    def agents_involved(self) -> list[str]:
        return [
            state.agent.value
            for state in self.agent_states
            if state.decisions_made > 0
        ]
