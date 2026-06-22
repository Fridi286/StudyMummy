from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    file_name: str
    storage_path: str


class DocumentResponse(DocumentBase):
    document_id: str
    user_id: str
    tags: list[str] = []
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentTagsUpdate(BaseModel):
    tags: list[str]

class TaskResponse(BaseModel):
    task_id: str
    document_id: str
    difficulty: int
    task_text: str
    key_concepts: list[str]
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class QuizQuestionResponse(BaseModel):
    question_id: str
    question_text: str
    options: list[str]
    correct_answer: str
    explanation: str | None = None
    key_concepts: list[str] = []
    
    model_config = ConfigDict(from_attributes=True)

class QuizResponse(BaseModel):
    quiz_id: str
    document_id: str
    title: str
    created_at: datetime
    questions: list[QuizQuestionResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class CheatsheetResponse(BaseModel):
    cheatsheet_id: str
    document_id: str
    title: str
    content: str
    key_concepts: list[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TaskStatusUpdate(BaseModel):
    status: str

class QuizAttemptRequest(BaseModel):
    answers: dict[str, str]

class QuizAttemptResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score: int
    total_questions: int
    answers: dict[str, str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
