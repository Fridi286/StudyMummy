import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import cast
from openai.types.chat import ChatCompletionMessageParam

from app.models.memory import WorkingMemory, DialogTurn, LearningProfile
from app.db.models import Session, ChatLog, LearningProfile as DbLearningProfile, ConfidenceScore, Topic
from app.core.logging import get_logger

log = get_logger(__name__)

async def get_or_create_session(db: AsyncSession, session_id: str, user_id: str) -> WorkingMemory:
    stmt = (
        select(Session)
        .options(selectinload(Session.chat_logs))
        .where(Session.session_id == session_id)
    )
    result = await db.execute(stmt)
    db_session = result.scalars().first()

    if not db_session:
        db_session = Session(session_id=session_id, user_id=user_id)
        db.add(db_session)
        await db.commit()
        await db.refresh(db_session)
        log.info(f"Session created in DB: {session_id}")
        chat_logs = []
    else:
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
        select(ConfidenceScore, Topic.name)
        .join(Topic, ConfidenceScore.topic_id == Topic.topic_id)
        .where(ConfidenceScore.user_id == user_id)
    )
    scores_result = await db.execute(scores_stmt)
    
    confidence_scores: dict[str, float] = {}
    for row in scores_result.all():
        score_obj = cast(ConfidenceScore, row[0])
        topic_name = cast(str, row[1])
        confidence_scores[topic_name] = float(score_obj.confidence)

    return LearningProfile(
        user_id=db_profile.user_id,
        confidence_scores=confidence_scores,
        error_patterns=db_profile.error_patterns or [],
        sessions_count=db_profile.sessions_count,
        last_seen=db_profile.last_seen
    )


async def update_profile(db: AsyncSession, user_id: str, topic_name: str, score: float) -> LearningProfile:
    # First ensure profile exists and update last_seen
    _ = await get_or_create_profile(db, user_id)
    
    update_stmt = (
        update(DbLearningProfile)
        .where(DbLearningProfile.user_id == user_id)
        .values(last_seen=datetime.now(timezone.utc))
    )
    _ = await db.execute(update_stmt)

    # Find the topic_id by name (assuming topic exists for this operation, otherwise this is a no-op or would require creation)
    topic_stmt = select(Topic).where(Topic.name == topic_name)
    topic_result = await db.execute(topic_stmt)
    topic = topic_result.scalars().first()

    if topic:
        # Check if confidence score exists
        cs_stmt = select(ConfidenceScore).where(
            ConfidenceScore.user_id == user_id,
            ConfidenceScore.topic_id == topic.topic_id
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
                subject_id=topic.subject_id,
                topic_id=topic.topic_id,
                confidence=clamped_score
            )
            db.add(new_cs)

    await db.commit()
    return await get_or_create_profile(db, user_id)
