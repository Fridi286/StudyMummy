from pydantic import BaseModel, Field

# -------------------------------------------------------------------
# Task Generation Schemas
# -------------------------------------------------------------------
class GeneratedTask(BaseModel):
    task_text: str = Field(description="The actual problem description or exercise extracted from the document.")
    difficulty: int = Field(description="Estimated difficulty from 1 (easiest) to 5 (hardest).", ge=1, le=5)
    key_concepts: list[str] = Field(description="List of key concepts or formulas needed to solve this task.")

class TaskGenerationSchema(BaseModel):
    tasks: list[GeneratedTask] = Field(description="List of all actionable exercises or problems extracted from the document.")

# -------------------------------------------------------------------
# Quiz Generation Schemas
# -------------------------------------------------------------------
class QuizQuestionSchema(BaseModel):
    question_text: str = Field(description="The multiple-choice question.")
    options: list[str] = Field(description="Exactly 4 possible answers.", min_length=4, max_length=4)
    correct_answer: str = Field(description="The correct answer (must exactly match one of the options).")
    explanation: str = Field(description="Brief explanation of why the answer is correct.")
    key_concepts: list[str] = Field(description="List of key concepts or formulas needed to solve this question.")

class QuizGenerationSchema(BaseModel):
    title: str = Field(description="A catchy title for the quiz based on the document content.")
    questions: list[QuizQuestionSchema] = Field(description="List of 5 to 10 multiple-choice questions.")

# -------------------------------------------------------------------
# Cheatsheet Generation Schemas
# -------------------------------------------------------------------
class CheatsheetGenerationSchema(BaseModel):
    title: str = Field(description="A descriptive title for the cheatsheet.")
    content: str = Field(description="The main cheatsheet content formatted in Markdown. Should include definitions, formulas, and summaries.")
    key_concepts: list[str] = Field(description="A list of 5 to 15 key terms or concepts covered in this cheatsheet.")

# -------------------------------------------------------------------
# Tag Generation Schemas
# -------------------------------------------------------------------
class TagGenerationSchema(BaseModel):
    tags: list[str] = Field(description="A list of 3-5 highly specific, granular semantic concepts or topics covered in the document.")
