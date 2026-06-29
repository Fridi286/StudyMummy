import uuid
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict

from app.db.session import get_async_db
from app.db.models import User, CalendarNote
from app.api.dependencies import get_current_user

router = APIRouter()

class CalendarNoteBase(BaseModel):
    title: str
    content: str
    start_time: datetime
    end_time: datetime

class CalendarNoteCreate(CalendarNoteBase):
    pass

class CalendarNoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

class CalendarNoteResponse(CalendarNoteBase):
    note_id: str
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=list[CalendarNoteResponse])
async def list_calendar_notes(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    stmt = select(CalendarNote).where(CalendarNote.user_id == current_user.user_id).order_by(CalendarNote.start_time)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=CalendarNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_note(
    note_in: CalendarNoteCreate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    note = CalendarNote(
        note_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        title=note_in.title,
        content=note_in.content,
        start_time=note_in.start_time,
        end_time=note_in.end_time,
        created_at=datetime.now(timezone.utc)
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

@router.put("/{note_id}", response_model=CalendarNoteResponse)
async def update_calendar_note(
    note_id: str,
    note_in: CalendarNoteUpdate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    stmt = select(CalendarNote).where(
        (CalendarNote.note_id == note_id) & 
        (CalendarNote.user_id == current_user.user_id)
    )
    result = await db.execute(stmt)
    note = result.scalars().first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    update_data = note_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
        
    await db.commit()
    await db.refresh(note)
    return note

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_note(
    note_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    stmt = select(CalendarNote).where(
        (CalendarNote.note_id == note_id) & 
        (CalendarNote.user_id == current_user.user_id)
    )
    result = await db.execute(stmt)
    note = result.scalars().first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    await db.delete(note)
    await db.commit()
