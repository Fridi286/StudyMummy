"""Agent API: observable multi-agent tutoring and lightweight text extraction."""
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.agent import (
    ChatRequest, ChatResponse,
    DocumentUploadResponse,
    QuizRequest, QuizResponse,
    CheatsheetRequest, CheatsheetResponse,
)
from app.services.llm_service import LLMService, filter_user_input
from app.agents.orchestrator import AgentOrchestrator
from app.agents.protocol import AgentContext, AgentStep
from app.services.rag_service import RAGService, get_rag_service
from app.core.context import current_user_id
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from app.api.dependencies import get_current_user
from app.db.models import Document, Task, User
from app.services.session_service import (
    get_or_create_session, append_dialog,
    get_dialog_as_messages, update_session_context,
)
from app.core.logging import get_logger, get_trace_id
from app.db.models import Session as DbSession, ChatLog
from sqlalchemy import select, desc

log = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent"])

_llm = LLMService()
_orchestrator = AgentOrchestrator(_llm)


async def _resolve_study_context(
    db: AsyncSession,
    user_id: str,
    task_id: str | None,
    document_id: str | None,
) -> tuple[str | None, str | None]:
    """Resolve trusted task context and enforce document ownership."""
    if task_id:
        stmt = (
            select(Task)
            .join(Document, Document.document_id == Task.document_id)
            .where(Task.task_id == task_id, Document.user_id == user_id)
        )
        task = (await db.execute(stmt)).scalars().first()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if document_id and document_id != task.document_id:
            raise HTTPException(status_code=400, detail="Task does not belong to the selected document")
        context = "\n".join(
            [
                f"Aufgabe: {task.task_text}",
                f"Schwierigkeit: {task.difficulty}/5",
                f"Schluesselkonzepte: {', '.join(task.key_concepts) if task.key_concepts else 'nicht angegeben'}",
                f"Bearbeitungsstatus: {task.status}",
            ]
        )
        return task.document_id, context

    if document_id:
        stmt = select(Document.document_id).where(
            Document.document_id == document_id,
            Document.user_id == user_id,
        )
        if (await db.execute(stmt)).scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Document not found")
    return document_id, None


def _infer_help_level(message: str, current_level: int) -> int:
    text = message.lower()
    solution_markers = ("lösung", "loesung", "musterlösung", "musterloesung", "auflösen", "aufloesen")
    step_markers = ("schritt", "step by step", "rechne vor", "vormachen")
    hint_markers = ("hint", "hinweis", "tipp", "hilfe", "hilf")
    stuck_markers = ("weiß nicht", "weiss nicht", "keine ahnung", "verstehe nicht", "komme nicht weiter")

    if any(marker in text for marker in solution_markers):
        return 4
    if any(marker in text for marker in step_markers):
        return max(current_level, 3)
    if any(marker in text for marker in hint_markers):
        return min(4, max(current_level + 1, 2))
    if any(marker in text for marker in stuck_markers):
        return min(4, current_level + 1)
    return min(4, max(1, current_level))


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


@router.post("/chat", response_model=ChatResponse, summary="Kooperativer MAS-Tutor-Chat")
async def chat(
    req: ChatRequest,
    rag: Annotated[RAGService, Depends(get_rag_service)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Hauptendpunkt: Planner, Tutor und Reviewer koordinieren den nächsten
    sokratischen Lernschritt über typisierte Nachrichten. Toolrechte bleiben
    auf das eng erlaubte Subset dieses Turns begrenzt.
    """
    try:
        message = filter_user_input(req.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    document_id, task_context = await _resolve_study_context(
        db,
        current_user.user_id,
        req.task_id,
        req.document_id,
    )
    try:
        session = await get_or_create_session(db, req.session_id, current_user.user_id, req.task_id)
    except PermissionError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    help_level = _infer_help_level(req.message, session.help_level)
    clear_current_task = req.document_id is not None and req.task_id is None
    active_task_id = None if clear_current_task else (req.task_id or session.current_task_id)
    session = await update_session_context(
        db,
        req.session_id,
        current_user.user_id,
        current_task_id=active_task_id,
        help_level=help_level,
        clear_current_task=clear_current_task,
    )

    await append_dialog(db, req.session_id, "user", message)

    # RAG-Kontext holen (pgvector)
    retrieval_query = f"{task_context}\n\nNutzerfrage: {message}" if task_context else message
    rag_context = await rag.retrieve(
        db,
        current_user.user_id,
        retrieval_query,
        document_id=document_id,
    )

    messages = await get_dialog_as_messages(db, req.session_id, current_user.user_id)
    # Bind identity only for the execution window of side-effecting tools.
    user_context_token = current_user_id.set(current_user.user_id)
    try:
        result = await _orchestrator.run(
            AgentContext(
                user_id=current_user.user_id,
                session_id=req.session_id,
                message=message,
                help_level=session.help_level,
                current_task_id=session.current_task_id,
                document_id=document_id,
                task_context=task_context,
                extra_context=req.extra_context,
                rag_context=rag_context,
                history=messages,
                current_time=datetime.now(timezone.utc).isoformat(),
            )
        )
    finally:
        current_user_id.reset(user_context_token)

    await append_dialog(
        db,
        req.session_id,
        "assistant",
        result.response,
        action_taken=result.plan.action.value,
    )
    result.steps.append(AgentStep(
        agent="memory",
        phase="remember",
        summary="Finale MAS-Antwort und ausgeführte Aktion im episodischen Sitzungsverlauf gespeichert.",
        round=result.coordination_rounds,
    ))
    return ChatResponse(
        session_id=req.session_id,
        message=result.response,
        action_taken=result.plan.action.value,
        tool_calls=result.tool_calls,
        tool_observations=result.tool_observations,
        trace_id=get_trace_id(),
        decision=result.plan,
        agent_trace=result.steps,
        communications=result.communications,
        agent_states=result.agent_states,
        agents_involved=result.agents_involved,
        coordination_rounds=result.coordination_rounds,
        reviewed=result.reviewed,
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
    # Note: Vector embeddings and database storage are now handled via the main /documents/ upload background task.

    tasks = await _llm.extract_tasks_from_text(text)

    return DocumentUploadResponse(
        document_id=doc_id,
        extracted_tasks=tasks,
        message=f"{len(tasks)} Aufgabe(n) aus '{file.filename}' extrahiert.",
    )
