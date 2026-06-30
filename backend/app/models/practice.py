from pydantic import BaseModel, Field
from typing import Literal


class PracticeTaskRequest(BaseModel):
    document_ids: list[str] = Field(min_length=1)
    difficulty: int = Field(ge=1, le=5)
    tags: list[str] = []
    text_filter: str = ""


class PracticeTaskResponse(BaseModel):
    practice_task_id: str
    task_type: Literal["text", "multiple_choice"]
    context_excerpt: str = ""
    question: str
    options: list[str] = []
    difficulty: int
    key_concepts: list[str] = []
    source_document_ids: list[str]
    reward_coins: int = 5


class PracticeAnswerRequest(BaseModel):
    practice_task_id: str
    answer: str = Field(min_length=1)


class PracticeAnswerResponse(BaseModel):
    practice_task_id: str
    feedback: str
    correct: bool | None = None
    awarded_coins: int
    reference_answer: str | None = None
