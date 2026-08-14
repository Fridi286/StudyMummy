"""
Request/Response-Modelle für alle Agent-Endpunkte.
"""
from typing import Annotated, Optional
from pydantic import BaseModel, Field, StringConstraints

from app.agents.protocol import (
    AgentCommunication,
    AgentLocalState,
    AgentPlan,
    AgentStep,
    ToolObservation,
)


class ChatRequest(BaseModel):
    session_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    task_id: Annotated[Optional[str], StringConstraints(strip_whitespace=True, max_length=255)] = None
    document_id: Annotated[Optional[str], StringConstraints(strip_whitespace=True, max_length=255)] = None
    extra_context: Annotated[Optional[str], StringConstraints(strip_whitespace=True, max_length=12000)] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    action_taken: Optional[str] = None   # z. B. "hint_given", "task_solved"
    tool_calls: list[str] = Field(default_factory=list)
    tool_observations: list[ToolObservation] = Field(default_factory=list)
    trace_id: str
    decision: AgentPlan
    agent_trace: list[AgentStep] = Field(default_factory=list)
    communications: list[AgentCommunication] = Field(default_factory=list)
    agent_states: list[AgentLocalState] = Field(default_factory=list)
    agents_involved: list[str] = Field(default_factory=list)
    coordination_rounds: int = 1
    reviewed: bool = False


class ExtractedTask(BaseModel):
    task_id: str
    tags: list[str]
    difficulty: int
    task_text: str
    required_concepts: list[str]
    status: str = "open"


class QuizQuestion(BaseModel):
    id: str
    text: str
    options: list[str]
    correct: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    extracted_tasks: list[ExtractedTask]
    message: str


class QuizRequest(BaseModel):
    user_id: str
    topic: str
    num_questions: int = 5


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]
    topic: str


class CheatsheetRequest(BaseModel):
    user_id: str
    session_id: str


class CheatsheetResponse(BaseModel):
    content: str
    topics_covered: list[str]
