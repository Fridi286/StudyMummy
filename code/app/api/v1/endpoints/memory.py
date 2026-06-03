"""
Memory-Endpunkte: Session-Zustand und Lernprofile.
"""
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.db.session import get_async_db
from app.db.models import User
from app.services.session_service import (
    get_or_create_session, get_or_create_profile,
)
from app.models.memory import WorkingMemory, LearningProfile

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/session/{session_id}", response_model=WorkingMemory)
async def get_session(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> WorkingMemory:
    """Gibt das aktuelle Working Memory einer Session zurück."""
    return await get_or_create_session(db, session_id, current_user.user_id)


@router.get("/profile", response_model=LearningProfile)
async def get_profile(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> LearningProfile:
    """Gibt das Lernprofil des aktuellen Nutzers zurück."""
    return await get_or_create_profile(db, current_user.user_id)
