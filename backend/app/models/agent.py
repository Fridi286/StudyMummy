"""
Request/Response-Modelle für alle Agent-Endpunkte.
"""
from typing import Annotated, Optional
from pydantic import BaseModel, StringConstraints


class ChatRequest(BaseModel):
    session_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    task_id: Optional[str] = None
    extra_context: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    action_taken: Optional[str] = None   # z. B. "hint_given", "task_solved"
    tool_calls: list[str] = []
    trace_id: str


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
