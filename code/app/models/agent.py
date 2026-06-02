"""
Request/Response-Modelle für alle Agent-Endpunkte.
"""
from typing import Optional, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str
    task_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    action_taken: Optional[str] = None   # z. B. "hint_given", "task_solved"
    tool_calls: list[str] = []
    trace_id: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    extracted_tasks: list[dict[str, Any]]
    message: str


class QuizRequest(BaseModel):
    user_id: str
    topic: str
    num_questions: int = 5


class QuizResponse(BaseModel):
    questions: list[dict[str, Any]]
    topic: str


class CheatsheetRequest(BaseModel):
    user_id: str
    session_id: str


class CheatsheetResponse(BaseModel):
    content: str
    topics_covered: list[str]
