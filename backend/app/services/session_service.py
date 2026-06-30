import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import cast
from openai.types.chat import ChatCompletionMessageParam

from app.models.memory import WorkingMemory, DialogTurn, LearningProfile
from app.db.models import Session, ChatLog, LearningProfile as DbLearningProfile, ConfidenceScore
from app.core.logging import get_logger

log = get_logger(__name__)

async def get_or_create_session(db: AsyncSession, session_id: str, user_id: str, task_id: str | None = None) -> WorkingMemory:
    stmt = (
        select(Session)
        .options(selectinload(Session.chat_logs))
        .where(Session.session_id == session_id)
    )
    result = await db.execute(stmt)
    db_session = result.scalars().first()

    if not db_session:
        db_session = Session(session_id=session_id, user_id=user_id, current_task_id=task_id)
        db.add(db_session)
        await db.commit()
        await db.refresh(db_session)
        log.info(f"Session created in DB: {session_id}")
        chat_logs = []
    else:
        # Update the task_id in the database if a new one is provided
        if task_id and db_session.current_task_id != task_id:
            db_session.current_task_id = task_id
            await db.commit()

        chat_logs = db_session.chat_logs or []

    dialog_history = [
        DialogTurn(role=log.role, content=log.content, timestamp=log.timestamp)
        for log in chat_logs
    ]
    return WorkingMemory(
        session_id=db_session.session_id,
        current_task_id=db_session.current_task_id,
        help_level=db_session.help_level,
        dialog_history=dialog_history,
        intermediate_steps=[]
    )


async def append_dialog(db: AsyncSession, session_id: str, role: str, content: str) -> None:
    chat_log = ChatLog(
        message_id=str(uuid.uuid4()),
        session_id=session_id,
        role=role,
        content=content
    )
    db.add(chat_log)
    await db.commit()


async def update_session_context(
    db: AsyncSession,
    session_id: str,
    user_id: str,
    current_task_id: str | None = None,
    help_level: int | None = None,
) -> WorkingMemory:
    await get_or_create_session(db, session_id, user_id)

    values: dict[str, str | int | None] = {}
    if current_task_id is not None:
        values["current_task_id"] = current_task_id
    if help_level is not None:
        values["help_level"] = min(4, max(1, help_level))

    if values:
        await db.execute(
            update(Session)
            .where(Session.session_id == session_id, Session.user_id == user_id)
            .values(**values)
        )
        await db.commit()

    return await get_or_create_session(db, session_id, user_id)


async def get_dialog_as_messages(db: AsyncSession, session_id: str, user_id: str) -> list[ChatCompletionMessageParam]:
    wm = await get_or_create_session(db, session_id, user_id)
    messages: list[ChatCompletionMessageParam] = []
    for t in wm.dialog_history:
        if t.role == "user":
            messages.append({"role": "user", "content": t.content})
        elif t.role == "assistant":
            messages.append({"role": "assistant", "content": t.content})
        elif t.role == "system":
            messages.append({"role": "system", "content": t.content})
    return messages

async def get_or_create_profile(db: AsyncSession, user_id: str) -> LearningProfile:
    stmt = (
        select(DbLearningProfile)
        .where(DbLearningProfile.user_id == user_id)
    )
    result = await db.execute(stmt)
    db_profile = result.scalars().first()

    if not db_profile:
        db_profile = DbLearningProfile(user_id=user_id)
        db.add(db_profile)
        await db.commit()
        await db.refresh(db_profile)
    
    # Load confidence scores
    scores_stmt = (
        select(ConfidenceScore)
        .where(ConfidenceScore.user_id == user_id)
    )
    scores_result = await db.execute(scores_stmt)
    
    confidence_scores: dict[str, float] = {}
    for score_obj in scores_result.scalars().all():
        confidence_scores[score_obj.tag] = float(score_obj.confidence)

    return LearningProfile(
        user_id=db_profile.user_id,
        confidence_scores=confidence_scores,
        error_patterns=db_profile.error_patterns or [],
        sessions_count=db_profile.sessions_count,
        last_seen=db_profile.last_seen
    )


async def update_profile(db: AsyncSession, user_id: str, tag: str, score: float) -> LearningProfile:
    # First ensure profile exists and update last_seen
    _ = await get_or_create_profile(db, user_id)
    
    update_stmt = (
        update(DbLearningProfile)
        .where(DbLearningProfile.user_id == user_id)
        .values(last_seen=datetime.now(timezone.utc))
    )
    _ = await db.execute(update_stmt)

    tag_lower = tag.strip().lower()

    # Check if confidence score exists
    cs_stmt = select(ConfidenceScore).where(
        ConfidenceScore.user_id == user_id,
        ConfidenceScore.tag == tag_lower
    )
    cs_result = await db.execute(cs_stmt)
    cs = cs_result.scalars().first()

    clamped_score = round(min(1.0, max(0.0, score)), 2)
    if cs:
        cs.confidence = clamped_score
        cs.updated_at = datetime.now(timezone.utc)
    else:
        new_cs = ConfidenceScore(
            score_id=str(uuid.uuid4()),
            user_id=user_id,
            tag=tag_lower,
            confidence=clamped_score
        )
        db.add(new_cs)

    await db.commit()
    return await get_or_create_profile(db, user_id)
