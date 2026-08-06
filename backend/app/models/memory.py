"""Models for working, episodic, and semantic memory."""
from datetime import datetime, timezone
from typing import ClassVar

from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import TypedDict

class EpisodicEventPayload(TypedDict, total=False):
    score: float
    hint_text: str
    error_message: str
    user_answer: str


class DialogTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkingMemory(BaseModel):
    """Kurzzeitgedächtnis: aktive Aufgabe + aktueller Dialog."""
    session_id: str
    current_task_id: str | None = None
    help_level: int = Field(default=1, ge=1, le=4)
    dialog_history: list[DialogTurn] = Field(default_factory=list)
    intermediate_steps: list[str] = Field(default_factory=list)

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)





class EpisodicEvent(BaseModel):
    """Einzelnes Ereignis für das episodische Gedächtnis."""
    session_id: str
    task_id: str
    event_type: str  # "solved", "error", "hint_given", "quiz_result"
    payload: EpisodicEventPayload = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LearningProfile(BaseModel):
    """Langzeit-Nutzerprofil mit Confidence-Werten pro Thema."""
    user_id: str
    confidence_scores: dict[str, float] = Field(default_factory=dict)   # topic → 0.0–1.0
    error_patterns: list[str] = Field(default_factory=list)
    sessions_count: int = 0
    last_seen: datetime | None = None
