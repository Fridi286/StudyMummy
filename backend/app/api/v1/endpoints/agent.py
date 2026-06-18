"""
Agent-Endpunkte: Chat, Dokument-Upload, Quiz, Cheatsheet.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.agent import (
    ChatRequest, ChatResponse,
    DocumentUploadResponse,
    QuizRequest, QuizResponse,
    CheatsheetRequest, CheatsheetResponse,
)
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService, get_rag_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.api.dependencies import get_current_user
from app.db.models import User
from app.services.session_service import (
    get_or_create_session, append_dialog,
    get_dialog_as_messages,
)
from app.core.logging import get_logger, get_trace_id
from app.db.models import Session as DbSession, ChatLog
from sqlalchemy import select, desc

log = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent"])

_llm = LLMService()


@router.get("/sessions", summary="List user's chat sessions")
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    stmt = (
        select(DbSession)
        .where(DbSession.user_id == current_user.user_id)
        .order_by(desc(DbSession.created_at))
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    return [
        {
            "session_id": s.session_id,
            "created_at": s.created_at,
            "active": s.active,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages", summary="Load messages for a session")
async def get_session_messages(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Verify ownership
    stmt = select(DbSession).where(
        DbSession.session_id == session_id,
        DbSession.user_id == current_user.user_id
    )
    session = (await db.execute(stmt)).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msg_stmt = select(ChatLog).where(ChatLog.session_id == session_id).order_by(ChatLog.timestamp)
    messages = (await db.execute(msg_stmt)).scalars().all()

    return [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in messages]


@router.delete("/sessions/{session_id}", summary="Delete a chat session")
async def delete_session(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    stmt = select(DbSession).where(
        DbSession.session_id == session_id,
        DbSession.user_id == current_user.user_id
    )
    session = (await db.execute(stmt)).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted"}


@router.post("/chat", response_model=ChatResponse, summary="Sokratischer Tutor-Chat")
async def chat(
    req: ChatRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Hauptendpunkt: Nutzer schreibt eine Nachricht, der Agent antwortet sokratisch
    und nutzt bei Bedarf Tools (evaluate_answer, update_learning_profile, award_coins).
    """
    # Working Memory auffrischen
    session = await get_or_create_session(db, req.session_id, current_user.user_id)
    if req.task_id:
        session.current_task_id = req.task_id

    # Nachricht ins Gedächtnis
    await append_dialog(db, req.session_id, "user", req.message)

    # RAG-Kontext holen
    context = rag.retrieve(req.message)

    # Dialog-History für LLM
    messages = await get_dialog_as_messages(db, req.session_id, current_user.user_id)

    # LLM-Aufruf mit Tool Use
    reply, tools_called = await _llm.chat_with_tools(
        messages=messages,
        extra_context=context or None,
    )

    await append_dialog(db, req.session_id, "assistant", reply)

    return ChatResponse(
        session_id=req.session_id,
        message=reply,
        action_taken=tools_called[-1] if tools_called else None,
        tool_calls=tools_called,
        trace_id=get_trace_id(),
    )


@router.post("/upload", response_model=DocumentUploadResponse, summary="Dokument hochladen & Aufgaben extrahieren")
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    rag: Annotated[RAGService, Depends(get_rag_service)]
):
    """
    Perception-Schicht: Lädt ein Dokument hoch, extrahiert Text,
    fügt ihn dem RAG-Vektorspeicher hinzu und gibt strukturierte Aufgaben zurück.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Kein Dateiname")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Leere Datei hochgeladen")
    
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1", errors="replace")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Datei enthält keinen auswertbaren Text")

    doc_id = file.filename.replace(" ", "_")
    rag.add_document(doc_id=doc_id, text=text, metadata={"filename": file.filename})

    tasks = await _llm.extract_tasks_from_text(text)

    return DocumentUploadResponse(
        document_id=doc_id,
        extracted_tasks=tasks,
        message=f"{len(tasks)} Aufgabe(n) aus '{file.filename}' extrahiert.",
    )


@router.post("/quiz", response_model=QuizResponse, summary="Quiz generieren")
async def generate_quiz(req: QuizRequest):
    """Action-Schicht: Generiert ein Quiz zu einem Thema."""
    from app.tools.study_tools import _generate_quiz_questions
    result = await _generate_quiz_questions(
        topic=req.topic,
        num_questions=req.num_questions,
    )
    return QuizResponse(questions=result["questions"], topic=result["topic"])


@router.post("/cheatsheet", response_model=CheatsheetResponse, summary="Cheatsheet erstellen")
async def create_cheatsheet(
    req: CheatsheetRequest,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Action-Schicht: Erstellt ein personalisiertes Cheatsheet nach der Lerneinheit."""
    from app.services.session_service import get_or_create_session
    from app.tools.study_tools import _create_cheatsheet

    session = await get_or_create_session(db, req.session_id, current_user.user_id)
    topics = ["Allgemeine Konzepte"]  # TODO: aus Lernprofil laden
    result = await _create_cheatsheet(
        user_id=req.user_id,
        session_id=req.session_id,
        topics=topics,
    )
    return CheatsheetResponse(content=result["content"], topics_covered=topics)
