"""
Pydantic models for persistent tasks.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import TaskStatus


class TaskCreate(BaseModel):
    document_id: str
    difficulty: int = Field(ge=1, le=5)
    task_text: str
    key_concepts: list[str] = []
    status: TaskStatus = TaskStatus.open


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)


class TaskResponse(TaskCreate):
    task_id: str

    model_config = ConfigDict(from_attributes=True)
