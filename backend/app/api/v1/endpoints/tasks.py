"""
Task endpoints backed by PostgreSQL.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.models import Document, Task, User
from app.db.session import get_async_db
from app.models.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()


async def _get_user_task_or_404(
    task_id: str,
    db: AsyncSession,
    current_user: User,
) -> Task:
    stmt = (
        select(Task)
        .join(Document)
        .where(
            Task.task_id == task_id,
            Document.user_id == current_user.user_id,
        )
    )
    result = await db.execute(stmt)
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    return task


@router.get("/", response_model=list[TaskResponse], summary="Alle Aufgaben des Nutzers")
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    stmt = (
        select(Task)
        .join(Document)
        .where(Document.user_id == current_user.user_id)
        .order_by(Task.task_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await _get_user_task_or_404(task_id, db, current_user)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_create: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    document_stmt = select(Document).where(
        Document.document_id == task_create.document_id,
        Document.user_id == current_user.user_id,
    )
    document = (await db.execute(document_stmt)).scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    task = Task(
        task_id=str(uuid.uuid4()),
        document_id=task_create.document_id,
        difficulty=task_create.difficulty,
        task_text=task_create.task_text,
        key_concepts=task_create.key_concepts,
        status=task_create.status.value,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    update: TaskUpdate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = await _get_user_task_or_404(task_id, db, current_user)
    if update.status is not None:
        task.status = update.status.value
    if update.difficulty is not None:
        task.difficulty = update.difficulty
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = await _get_user_task_or_404(task_id, db, current_user)
    await db.delete(task)
    await db.commit()
