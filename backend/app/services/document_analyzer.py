import os
import subprocess
import uuid
import pymupdf  # PyMuPDF
import typing
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import textwrap

from app.db.models import Document, Task, Quiz, QuizQuestion, Cheatsheet, DocumentChunk
from app.models.generation import TaskGenerationSchema, QuizGenerationSchema, CheatsheetGenerationSchema, TagGenerationSchema
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


async def _notify_document_analysis(user_id: str, document_id: str, success: bool, message: str) -> None:
    event_type = "DOCUMENT_ANALYZED" if success else "DOCUMENT_ANALYSIS_FAILED"
    payload = {
        "type": event_type,
        "message": document_id if success else message,
        "document_id": document_id,
    }
    await manager.send_personal_message(user_id, payload)


def _extract_text_from_file(file_path: str) -> str:
    """
    Helper function to extract text from a file based on its extension.
    """
    full_text = ""
    ext = os.path.splitext(file_path)[1].lower()
    text_extensions = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".py", ".js", ".ts", ".css"}
    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
    
    if ext in text_extensions:
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()
    elif ext in image_extensions:
        full_text = _extract_text_from_image(file_path)
    else:
        # Fallback to PyMuPDF for complex formats like PDF, EPUB, etc.
        doc = pymupdf.open(file_path)
        for i in range(len(doc)):
            page = typing.cast(pymupdf.Page, doc[i])
            page_text = str(page.get_text("text"))
            if not page_text.strip():
                page_text = _extract_text_from_pdf_page_with_ocr(page)
            full_text += page_text + "\n"
        doc.close()
        
    return full_text


def _extract_text_from_image(file_path: str) -> str:
    """
    Best-effort OCR for screenshots and scanned exercise images.
    """
    try:
        result = subprocess.run(
            ["tesseract", file_path, "stdout", "-l", "deu+eng"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            log.warning(f"OCR for image failed: {result.stderr.strip()}")
            return ""
        return result.stdout
    except Exception as e:
        log.warning(f"OCR for image failed or is unavailable: {e}")
        return ""


def _extract_text_from_pdf_page_with_ocr(page: pymupdf.Page) -> str:
    """
    Best-effort OCR fallback for scanned PDF pages.
    """
    try:
        textpage = page.get_textpage_ocr()
        return str(page.get_text("text", textpage=textpage))
    except Exception as e:
        log.warning(f"OCR for PDF page failed or is unavailable: {e}")
        return ""

async def analyze_document_background_task(
    document_id: str,
    file_path: str,
    user_id: str,
    tags_string: str = ""
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
            await _notify_document_analysis(
                user_id,
                document_id,
                False,
                "The uploaded file could not be read. Please try a PDF, text file, or a clearer image.",
            )
            return

        if not full_text.strip():
            log.warning("Extracted text is empty.")
            await _notify_document_analysis(
                user_id,
                document_id,
                False,
                "No readable text was found in this upload. Please try a text-based PDF, text file, or clearer screenshot.",
            )
            return
            
        # Limit text length to prevent massive token usage for now (e.g. max 20,000 chars)
        prompt_text = full_text[:20000]
        generated_artifact_count = 0

        # 1.2 Generate Semantic Tags
        log.info("Generating Semantic Tags...")
        user_tags = [t.strip().lower() for t in tags_string.split(",")] if tags_string.strip() else []
        final_tags = list(user_tags)
        try:
            tag_completion = await client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert tutor. Read the text and extract 3-5 highly specific, granular semantic concepts or topics covered in the document."},
                    {"role": "user", "content": prompt_text[:5000]} # Use first 5k chars for tagging
                ],
                response_format=TagGenerationSchema,
            )
            ai_tags_parsed = tag_completion.choices[0].message.parsed
            if ai_tags_parsed and ai_tags_parsed.tags:
                ai_tags = [t.lower().strip() for t in ai_tags_parsed.tags if t.strip()]
                final_tags = list(set(user_tags + ai_tags))
        except Exception as e:
            log.error(f"Failed to generate tags: {e}")
            
        if not final_tags:
            final_tags = ["general"]

        # 1.3 Update Document with Tags
        log.info("Updating Document tags...")
        try:
            from sqlalchemy import update
            await db.execute(update(Document).where(Document.document_id == document_id).values(tags=final_tags))
        except Exception as e:
            log.error(f"Failed to update document tags: {e}")

        # 1.5 Generate Embeddings and Chunks for RAG
        if settings.rag_embeddings_enabled:
            log.info("Generating embeddings and chunks for RAG...")
            try:
                # Simple chunking: split to ~1000 characters
                chunk_size = 1000
                chunks = textwrap.wrap(full_text, chunk_size, break_long_words=False, replace_whitespace=False)
                
                batch_size = 100
                chunk_index = 0
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    batch = [c.strip() for c in batch if c.strip()]
                    if not batch:
                        continue

                    response = await client.embeddings.create(
                        input=batch,
                        model=settings.embedding_model
                    )

                    for j, data in enumerate(response.data):
                        new_chunk = DocumentChunk(
                            chunk_id=str(uuid.uuid4()),
                            document_id=document_id,
                            user_id=user_id,
                            text=batch[j],
                            embedding=data.embedding,
                            chunk_index=chunk_index
                        )
                        db.add(new_chunk)
                        chunk_index += 1
                await db.commit()
                log.info(f"Saved {chunk_index} document chunks with embeddings.")
            except Exception as e:
                log.error(f"Failed to generate embeddings: {e}")
        else:
            log.info("RAG embeddings disabled; skipping document chunk embeddings.")

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
                        difficulty=t.difficulty,
                        task_text=t.task_text,
                        key_concepts=t.key_concepts,
                        status="open"
                    )
                    db.add(new_task)
                    generated_artifact_count += 1
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
                generated_artifact_count += 1
                
                for q in quiz_data.questions:
                    new_question = QuizQuestion(
                        question_id=str(uuid.uuid4()),
                        quiz_id=new_quiz.quiz_id,
                        question_text=q.question_text,
                        options=q.options,
                        correct_answer=q.correct_answer,
                        explanation=q.explanation,
                        key_concepts=q.key_concepts
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
                generated_artifact_count += 1
        except Exception as e:
            log.error(f"Failed to generate cheatsheet: {e}")

        # Commit all generated artifacts to the database
        log.info("Committing generated artifacts...")
        try:
            await db.commit()
        except Exception as e:
            log.error(f"Database commit failed: {e}")
            await db.rollback()
            await _notify_document_analysis(
                user_id,
                document_id,
                False,
                "The document was read, but the generated tasks could not be saved. Please try uploading it again.",
            )
            return

        if generated_artifact_count == 0:
            log.error(
                "Document %s was readable, but no generated artifacts were produced.",
                document_id,
            )
            await _notify_document_analysis(
                user_id,
                document_id,
                False,
                "Das Dokument wurde gelesen, aber die KI konnte keine Aufgaben, kein Quiz und kein Merkblatt erzeugen. Bitte prüfe Modell und API-Limit und versuche es erneut.",
            )
            return

        # 5. Notify Frontend via WebSocket
        log.info("Notifying frontend...")
        await _notify_document_analysis(user_id, document_id, True, "Document analysis completed.")
        
        log.info(f"Analysis complete for document {document_id}")
