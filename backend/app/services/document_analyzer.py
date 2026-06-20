import os
import uuid
import pymupdf  # PyMuPDF
import typing
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Document, Task, Quiz, QuizQuestion, Cheatsheet, Subject, Topic
from app.models.generation import TaskGenerationSchema, QuizGenerationSchema, CheatsheetGenerationSchema
from app.websockets.manager import manager
from app.db.session import AsyncSessionLocal
from app.core.logging import get_logger
from app.core.config import get_settings

log = get_logger(__name__)
settings = get_settings()

# Initialize OpenAI client using global settings (supports HAW fallback)
client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

def _extract_text_from_file(file_path: str) -> str:
    """
    Helper function to extract text from a file based on its extension.
    """
    full_text = ""
    ext = os.path.splitext(file_path)[1].lower()
    text_extensions = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".py", ".js", ".ts", ".css"}
    
    if ext in text_extensions:
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()
    else:
        # Fallback to PyMuPDF for complex formats like PDF, EPUB, etc.
        doc = pymupdf.open(file_path)
        for i in range(len(doc)):
            page = typing.cast(pymupdf.Page, doc[i])
            full_text += str(page.get_text("text")) + "\n"
        doc.close()
        
    return full_text

async def analyze_document_background_task(
    document_id: str,
    file_path: str,
    user_id: str
) -> None:
    """
    Background task to parse a document and generate AI content.
    """
    log.info(f"Starting analysis for document {document_id}")
    
    async with AsyncSessionLocal() as db:
        # 1. Extract Text
        try:
            full_text = _extract_text_from_file(file_path)
        except Exception as e:
            log.error(f"Failed to extract text from {file_path}: {e}")
            return

        if not full_text.strip():
            log.warning("Extracted text is empty.")
            return
            
        # We will need a default Subject and Topic for the Tasks. 
        # Let's get or create a default "General" subject and topic.
        subject_stmt = select(Subject).where(Subject.name == "General")
        subject_result = await db.execute(subject_stmt)
        subject = subject_result.scalars().first()
        
        if not subject:
            subject = Subject(subject_id=str(uuid.uuid4()), name="General")
            db.add(subject)
            await db.commit()
            await db.refresh(subject)
            
        topic_stmt = select(Topic).where((Topic.name == "General") & (Topic.subject_id == subject.subject_id))
        topic_result = await db.execute(topic_stmt)
        topic = topic_result.scalars().first()
        
        if not topic:
            topic = Topic(topic_id=str(uuid.uuid4()), name="General", subject_id=subject.subject_id)
            db.add(topic)
            await db.commit()
            await db.refresh(topic)

        # Limit text length to prevent massive token usage for now (e.g. max 20,000 chars)
        prompt_text = full_text[:20000]

        # 2. Generate Tasks
        log.info("Generating Tasks...")
        try:
            task_completion = await client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert tutor. Extract a list of actionable exercises or problems from the provided document text."},
                    {"role": "user", "content": prompt_text}
                ],
                response_format=TaskGenerationSchema,
            )
            task_data = task_completion.choices[0].message.parsed
            if task_data:
                for t in task_data.tasks:
                    new_task = Task(
                        task_id=str(uuid.uuid4()),
                        document_id=document_id,
                        subject_id=subject.subject_id,
                        topic_id=topic.topic_id,
                        difficulty=t.difficulty,
                        task_text=t.task_text,
                        required_concepts=t.required_concepts,
                        status="open"
                    )
                    db.add(new_task)
        except Exception as e:
            log.error(f"Failed to generate tasks: {e}")

        # 3. Generate Quiz
        log.info("Generating Quiz...")
        try:
            quiz_completion = await client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert tutor. Generate a multiple-choice quiz based on the provided document text."},
                    {"role": "user", "content": prompt_text}
                ],
                response_format=QuizGenerationSchema,
            )
            quiz_data = quiz_completion.choices[0].message.parsed
            if quiz_data:
                new_quiz = Quiz(
                    quiz_id=str(uuid.uuid4()),
                    document_id=document_id,
                    title=quiz_data.title
                )
                db.add(new_quiz)
                
                for q in quiz_data.questions:
                    new_question = QuizQuestion(
                        question_id=str(uuid.uuid4()),
                        quiz_id=new_quiz.quiz_id,
                        question_text=q.question_text,
                        options=q.options,
                        correct_answer=q.correct_answer,
                        explanation=q.explanation
                    )
                    db.add(new_question)
        except Exception as e:
            log.error(f"Failed to generate quiz: {e}")

        # 4. Generate Cheatsheet
        log.info("Generating Cheatsheet...")
        try:
            cheatsheet_completion = await client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert tutor. Create a comprehensive markdown cheatsheet summarizing the provided document text, extracting key concepts, definitions, and formulas."},
                    {"role": "user", "content": prompt_text}
                ],
                response_format=CheatsheetGenerationSchema,
            )
            cheatsheet_data = cheatsheet_completion.choices[0].message.parsed
            if cheatsheet_data:
                new_cheatsheet = Cheatsheet(
                    cheatsheet_id=str(uuid.uuid4()),
                    document_id=document_id,
                    title=cheatsheet_data.title,
                    content=cheatsheet_data.content,
                    key_concepts=cheatsheet_data.key_concepts
                )
                db.add(new_cheatsheet)
        except Exception as e:
            log.error(f"Failed to generate cheatsheet: {e}")

        # Commit all generated artifacts to the database
        log.info("Committing generated artifacts...")
        try:
            await db.commit()
        except Exception as e:
            log.error(f"Database commit failed: {e}")
            await db.rollback()

        # 5. Notify Frontend via WebSocket
        log.info("Notifying frontend...")
        await manager.send_personal_message(user_id, {
            "type": "DOCUMENT_ANALYZED",
            "message": document_id
        })
        
        log.info(f"Analysis complete for document {document_id}")
