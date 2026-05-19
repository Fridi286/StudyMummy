"""
Session-Service: verwaltet Working Memory pro Session (In-Memory für MVP).
"""
from datetime import datetime
from app.models.memory import WorkingMemory, DialogTurn, LearningProfile
from app.core.logging import get_logger

log = get_logger(__name__)

_sessions: dict[str, WorkingMemory] = {}
_profiles: dict[str, LearningProfile] = {}


def get_or_create_session(session_id: str) -> WorkingMemory:
    if session_id not in _sessions:
        _sessions[session_id] = WorkingMemory(session_id=session_id)
        log.info(f"Session created: {session_id}")
    return _sessions[session_id]


def append_dialog(session_id: str, role: str, content: str) -> None:
    session = get_or_create_session(session_id)
    session.dialog_history.append(DialogTurn(role=role, content=content))
    # Halte Window bei max 20 Turns
    if len(session.dialog_history) > 20:
        session.dialog_history = session.dialog_history[-20:]


def get_dialog_as_messages(session_id: str) -> list[dict]:
    session = get_or_create_session(session_id)
    return [{"role": t.role, "content": t.content} for t in session.dialog_history]


def get_or_create_profile(user_id: str) -> LearningProfile:
    if user_id not in _profiles:
        _profiles[user_id] = LearningProfile(user_id=user_id)
    return _profiles[user_id]


def update_profile(user_id: str, topic: str, score: float) -> LearningProfile:
    profile = get_or_create_profile(user_id)
    profile.confidence_scores[topic] = round(min(1.0, max(0.0, score)), 2)
    profile.last_seen = datetime.utcnow()
    return profile
