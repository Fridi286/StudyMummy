"""
Datenmodelle für Aufgaben (Perception-Output-Format aus Übungsblatt 02).
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    solved = "solved"
    repeat = "repeat"


class Task(BaseModel):
    task_id: str
    subject: str
    topic: str
    difficulty: int = Field(ge=1, le=5)
    task_text: str
    required_concepts: list[str] = []
    status: TaskStatus = TaskStatus.open


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
