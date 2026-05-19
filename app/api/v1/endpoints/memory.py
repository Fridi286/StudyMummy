"""
Memory-Endpunkte: Session-Zustand und Lernprofile.
"""
from fastapi import APIRouter, HTTPException
from app.services.session_service import (
    get_or_create_session, get_or_create_profile,
)
from app.models.memory import WorkingMemory, LearningProfile

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/session/{session_id}", response_model=WorkingMemory)
async def get_session(session_id: str):
    """Gibt das aktuelle Working Memory einer Session zurück."""
    return get_or_create_session(session_id)


@router.get("/profile/{user_id}", response_model=LearningProfile)
async def get_profile(user_id: str):
    """Gibt das Lernprofil eines Nutzers zurück."""
    return get_or_create_profile(user_id)
