"""
Agent-Endpunkte: Chat, Dokument-Upload, Quiz, Cheatsheet.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.agent import (
    ChatRequest, ChatResponse,
    DocumentUploadResponse,
    QuizRequest, QuizResponse,
    CheatsheetRequest, CheatsheetResponse,
)
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService, get_rag_service
from app.services.session_service import (
    get_or_create_session, append_dialog,
    get_dialog_as_messages,
)
from app.core.logging import get_logger, get_trace_id

log = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent"])

_llm = LLMService()


@router.post("/chat", response_model=ChatResponse, summary="Sokratischer Tutor-Chat")
async def chat(
    req: ChatRequest,
    rag: RAGService = Depends(get_rag_service),
):
    """
    Hauptendpunkt: Nutzer schreibt eine Nachricht, der Agent antwortet sokratisch
    und nutzt bei Bedarf Tools (evaluate_answer, update_learning_profile, award_coins).
    """
    # Working Memory auffrischen
    session = get_or_create_session(req.session_id)
    if req.task_id:
        session.current_task_id = req.task_id

    # Nachricht ins Gedächtnis
    append_dialog(req.session_id, "user", req.message)

    # RAG-Kontext holen
    context = rag.retrieve(req.message)

    # Dialog-History für LLM
    messages = get_dialog_as_messages(req.session_id)

    # LLM-Aufruf mit Tool Use
    reply, tools_called = await _llm.chat_with_tools(
        messages=messages,
        extra_context=context or None,
    )

    append_dialog(req.session_id, "assistant", reply)

    return ChatResponse(
        session_id=req.session_id,
        message=reply,
        action_taken=tools_called[-1] if tools_called else None,
        tool_calls=tools_called,
        trace_id=get_trace_id(),
    )


@router.post("/upload", response_model=DocumentUploadResponse, summary="Dokument hochladen & Aufgaben extrahieren")
async def upload_document(
    file: UploadFile = File(...),
    rag: RAGService = Depends(get_rag_service),
):
    """
    Perception-Schicht: Lädt ein Dokument hoch, extrahiert Text,
    fügt ihn dem RAG-Vektorspeicher hinzu und gibt strukturierte Aufgaben zurück.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Kein Dateiname")

    content = await file.read()
    
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1", errors="replace")

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
async def create_cheatsheet(req: CheatsheetRequest):
    """Action-Schicht: Erstellt ein personalisiertes Cheatsheet nach der Lerneinheit."""
    from app.services.session_service import get_or_create_session
    from app.tools.study_tools import _create_cheatsheet

    session = get_or_create_session(req.session_id)
    topics = ["Allgemeine Konzepte"]  # TODO: aus Lernprofil laden
    result = await _create_cheatsheet(
        user_id=req.user_id,
        session_id=req.session_id,
        topics=topics,
    )
    return CheatsheetResponse(content=result["content"], topics_covered=topics)
