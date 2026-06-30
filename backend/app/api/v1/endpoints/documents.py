import os
import uuid
import shutil
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_async_db
from app.db.models import User, Document, Task, Quiz, Cheatsheet
from app.api.dependencies import get_current_user
from app.models.document import (
    DocumentResponse, TaskResponse, QuizResponse, CheatsheetResponse,
    TaskStatusUpdate, QuizAttemptRequest, QuizAttemptResponse, DocumentTagsUpdate
)
from app.services.document_analyzer import analyze_document_background_task
from app.websockets.manager import manager

router = APIRouter()

UPLOAD_DIR = "data/documents"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tags_string: str = Form(""),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    # Check file size using FastAPI's built-in UploadFile.size
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 5MB limit."
        )

    # Generate a unique filename to prevent collisions
    file_extension = ""
    if file.filename and "." in file.filename:
        file_extension = f".{file.filename.split('.')[-1]}"
    
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save the file to the local filesystem
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Create the Document record in the DB
    document = Document(
        document_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        file_name=file.filename or "unknown_document",
        storage_path=file_path,
        uploaded_at=datetime.now(timezone.utc)
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Trigger AI analysis in the background
    # The service will create its own independent DB session to avoid lifecycle issues.
    background_tasks.add_task(analyze_document_background_task, document.document_id, file_path, current_user.user_id, tags_string)

    return document

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(Document.user_id == current_user.user_id).order_by(Document.uploaded_at.desc())
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    return documents

@router.get("/{document_id}/download", response_class=FileResponse)
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(
        (Document.document_id == document_id) & 
        (Document.user_id == current_user.user_id)
    )
    result = await db.execute(stmt)
    document = result.scalars().first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
        
    if not os.path.exists(document.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server."
        )
        
    return FileResponse(
        path=document.storage_path,
        filename=document.file_name,
        media_type="application/octet-stream"
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(
        (Document.document_id == document_id) & 
        (Document.user_id == current_user.user_id)
    )
    result = await db.execute(stmt)
    document = result.scalars().first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
        
    # Remove from filesystem
    if os.path.exists(document.storage_path):
        try:
            os.remove(document.storage_path)
        except Exception as e:
            # We can log the error, but we still want to delete the DB record
            print(f"Failed to delete file {document.storage_path}: {e}")
            
    # Delete from database
    await db.delete(document)
    await db.commit()

@router.put("/{document_id}/tags", response_model=DocumentResponse)
async def update_document_tags(
    document_id: str,
    update: DocumentTagsUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(
        (Document.document_id == document_id) & 
        (Document.user_id == current_user.user_id)
    )
    result = await db.execute(stmt)
    document = result.scalars().first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
        
    document.tags = update.tags
    await db.commit()
    await db.refresh(document)
    
    return document


@router.get("/{document_id}/tasks", response_model=list[TaskResponse])
async def get_document_tasks(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Task).where(Task.document_id == document_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{document_id}/quizzes", response_model=list[QuizResponse])
async def get_document_quizzes(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    # Use selectinload to eagerly load the questions relationship
    stmt = select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.document_id == document_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{document_id}/cheatsheets", response_model=list[CheatsheetResponse])
async def get_document_cheatsheets(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Cheatsheet).where(Cheatsheet.document_id == document_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.put("/tasks/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    update: TaskStatusUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Task).where(Task.task_id == task_id)
    result = await db.execute(stmt)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Optional: Verify task belongs to current user's document
    # stmt = select(Document).where(Document.document_id == task.document_id)
    # doc = (await db.execute(stmt)).scalars().first()
    # if doc.user_id != current_user.user_id: raise HTTPException(status_code=403, detail="Forbidden")

    if update.status == "completed" and not task.is_rewarded:
        reward = task.difficulty * 10
        
        # Calculate xp multiplier from active items
        from app.db.models import ActiveItem
        now_utc = datetime.now(timezone.utc)
        stmt_boosts = select(ActiveItem).where(
            ActiveItem.user_id == current_user.user_id,
            (ActiveItem.expires_at == None) | (ActiveItem.expires_at > now_utc)
        )
        active_boosts = (await db.execute(stmt_boosts)).scalars().all()
        
        xp_multiplier = 1.0
        for boost in active_boosts:
            if "xp_multiplier" in boost.effects:
                xp_multiplier *= float(boost.effects["xp_multiplier"])
                
        final_exp_reward = int(reward * xp_multiplier)
        
        current_user.coins += reward
        current_user.experience += final_exp_reward
        task.is_rewarded = True
        db.add(current_user)
        
        await manager.send_personal_message(current_user.user_id, {
            "type": "REWARD_GAINED",
            "coins": reward,
            "experience": final_exp_reward,
            "total_experience": current_user.experience,
            "reason": "Task Completed"
        })

    task.status = update.status
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/quizzes/{quiz_id}/attempts", response_model=QuizAttemptResponse)
async def submit_quiz_attempt(
    quiz_id: str,
    attempt_request: QuizAttemptRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    from app.db.models import QuizQuestion, QuizAttempt
    
    # 1. Fetch quiz questions to calculate score
    stmt = select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
    questions = (await db.execute(stmt)).scalars().all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="Quiz not found or has no questions")

    # 2. Calculate score
    score = 0
    total_questions = len(questions)
    correct_answers_map = {q.question_id: q.correct_answer for q in questions}
    
    for q_id, selected_opt in attempt_request.answers.items():
        if q_id in correct_answers_map and correct_answers_map[q_id] == selected_opt:
            score += 1
            
    # Check if first try
    stmt_attempts = select(func.count()).select_from(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id)
    result_attempts = await db.execute(stmt_attempts)
    previous_attempts_count = result_attempts.scalar_one()

    if previous_attempts_count == 0:
        # First try, reward based on performance (e.g., 20 coins/xp per correct answer)
        reward = score * 20
        
        # Calculate xp multiplier from active items
        from app.db.models import ActiveItem
        now_utc = datetime.now(timezone.utc)
        stmt_boosts = select(ActiveItem).where(
            ActiveItem.user_id == current_user.user_id,
            (ActiveItem.expires_at == None) | (ActiveItem.expires_at > now_utc)
        )
        active_boosts = (await db.execute(stmt_boosts)).scalars().all()
        
        xp_multiplier = 1.0
        for boost in active_boosts:
            if "xp_multiplier" in boost.effects:
                xp_multiplier *= float(boost.effects["xp_multiplier"])
                
        final_exp_reward = int(reward * xp_multiplier)
        
        current_user.coins += reward
        current_user.experience += final_exp_reward
        db.add(current_user)

        await manager.send_personal_message(current_user.user_id, {
            "type": "REWARD_GAINED",
            "coins": reward,
            "experience": final_exp_reward,
            "total_experience": current_user.experience,
            "reason": "Quiz Completed"
        })

    # 3. Save attempt
    attempt = QuizAttempt(
        attempt_id=str(uuid.uuid4()),
        quiz_id=quiz_id,
        score=score,
        total_questions=total_questions,
        answers=attempt_request.answers,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    
    return attempt


@router.get("/quizzes/{quiz_id}/attempts", response_model=list[QuizAttemptResponse])
async def get_quiz_attempts(
    quiz_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    from app.db.models import QuizAttempt
    stmt = select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id).order_by(QuizAttempt.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
