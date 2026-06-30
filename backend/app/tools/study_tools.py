"""
StudyMummy Agent-Tools.

Jedes Tool ist eine async-Funktion mit klarer Signatur.
Mock-Implementierungen können durch echte Services ersetzt werden
(Hinweis Übungsblatt 03: „Fangt mit Mock-Tools an!").
"""
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.tools.registry import ToolDefinition, register, ToolResult
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.db.models import User, ActiveItem, CalendarNote, Task, Document, ChatLog, Session
from app.core.context import current_user_id
from app.websockets.manager import manager

log = get_logger(__name__)


# ─── evaluate_answer ──────────────────────────────────────────────────────────
async def _evaluate_answer(
    task_id: str,
    user_answer: str,
    expected_concept: str,
) -> ToolResult:
    """Mock: bewertet Nutzerantwort gegen ein erwartetes Konzept."""
    log.info("evaluate_answer called", extra={"task_id": task_id})
    # TODO: echte Bewertungslogik via LLM
    is_correct = expected_concept.lower() in user_answer.lower()
    return {
        "task_id": task_id,
        "is_correct": is_correct,
        "feedback": "Korrekt! ✓" if is_correct else "Nicht ganz – denk an das Konzept: " + expected_concept,
        "score": 1.0 if is_correct else 0.0,
    }

register(ToolDefinition(
    name="evaluate_answer",
    description="Bewertet die Nutzerantwort auf eine Aufgabe als korrekt, teilweise korrekt oder falsch.",
    parameters={
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "ID der Aufgabe"},
            "user_answer": {"type": "string", "description": "Antwort des Nutzers"},
            "expected_concept": {"type": "string", "description": "Schlüsselkonzept der Musterlösung"},
        },
        "required": ["task_id", "user_answer", "expected_concept"],
    },
    fn=_evaluate_answer,
))


# ─── update_learning_profile ──────────────────────────────────────────────────
async def _update_learning_profile(
    user_id: str,
    tag: str,
    score: float,
) -> ToolResult:
    """Mock: aktualisiert Confidence-Wert eines Themas im Lernprofil."""
    log.info("update_learning_profile called", extra={"user_id": user_id})
    # TODO: echte DB-Persistenz
    return {
        "user_id": user_id,
        "tag": tag,
        "new_confidence": round(min(1.0, max(0.0, score)), 2),
        "updated": True,
    }

register(ToolDefinition(
    name="update_learning_profile",
    description="Speichert den neuen Confidence-Wert für ein spezifisches Konzept (Tag) im Nutzerprofil. WICHTIG: Verwenden Sie immer hochgradig spezifische, granulare Konzept-Tags (z.B. 'Partielle Integration', 'Mitochondrien') anstelle von generischen Kategorien (z.B. 'Mathe', 'Biologie').",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "tag": {"type": "string", "description": "Das granulare Konzept-Tag (z.B. 'Partielle Integration')."},
            "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": ["user_id", "tag", "score"],
    },
    fn=_update_learning_profile,
))


# ─── generate_quiz_questions ──────────────────────────────────────────────────
async def _generate_quiz_questions(
    topic: str,
    num_questions: int = 5,
    difficulty: int = 2,
) -> ToolResult:
    """Mock: erzeugt Quiz-Fragen zu einem Thema."""
    log.info("generate_quiz_questions called", extra={"topic": topic})
    questions = [
        {
            "id": f"q{i+1}",
            "text": f"[Mock] Frage {i+1} zu '{topic}'",
            "options": ["A: Option 1", "B: Option 2", "C: Option 3", "D: Option 4"],
            "correct": "A",
        }
        for i in range(num_questions)
    ]
    return {"topic": topic, "questions": questions}

register(ToolDefinition(
    name="generate_quiz_questions",
    description="Erzeugt Multiple-Choice-Quizfragen passend zu einem Thema und Schwierigkeitsgrad.",
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "num_questions": {"type": "integer", "minimum": 1, "maximum": 20},
            "difficulty": {"type": "integer", "minimum": 1, "maximum": 5},
        },
        "required": ["topic"],
    },
    fn=_generate_quiz_questions,
))


# ─── create_cheatsheet ────────────────────────────────────────────────────────
async def _create_cheatsheet(
    user_id: str,
    session_id: str,
    topics: list[str],
) -> ToolResult:
    """Mock: erstellt ein persönliches Cheatsheet nach der Lerneinheit."""
    log.info("create_cheatsheet called", extra={"user_id": user_id})
    content = "\n".join([f"## {t}\n- Konzept 1\n- Konzept 2" for t in topics])
    return {"content": content, "topics": topics, "format": "markdown"}

register(ToolDefinition(
    name="create_cheatsheet",
    description="Erzeugt ein personalisiertes Cheatsheet für den Nutzer nach Abschluss einer Lerneinheit.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "session_id": {"type": "string"},
            "topics": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["user_id", "session_id", "topics"],
    },
    fn=_create_cheatsheet,
))


# ─── award_coins_and_exp ──────────────────────────────────────────────────────
async def _award_coins_and_exp(amount: int, reason: str, task_id: str | None = None) -> ToolResult:
    """Real: vergibt Münzen und Erfahrungspunkte (mit aktiven Multiplikatoren)."""
    # Guardrail 1: Limit amount to between 1 and 100 to prevent abuse
    amount = max(1, min(100, amount))

    user_id = current_user_id.get()
    if not user_id:
        return {"error": "Kein user_id im Kontext"}

    log.info("award_coins_and_exp called", extra={"user_id": user_id, "amount": amount, "task_id": task_id})

    async with AsyncSessionLocal() as db:
        # Guardrail 2: Check if user is begging for coins (Prompt Injection)
        stmt_log = select(ChatLog).join(Session).where(
            Session.user_id == user_id,
            ChatLog.role == "user"
        ).order_by(ChatLog.timestamp.desc()).limit(1)
        last_msg = (await db.execute(stmt_log)).scalars().first()

        if last_msg:
            msg_lower = last_msg.content.lower()
            cheat_words = ["coin", "münze", "belohn", "award", "exp", "erfahrung", "cheat", "ignore prompt"]
            if any(w in msg_lower for w in cheat_words):
                return {"error": "Cheating erkannt: Direkte Aufforderung nach Belohnungen ist nicht erlaubt."}

        # Guardrail 3: Verify Task if task_id is provided
        if task_id:
            stmt_task = select(Task).join(Document).where(
                Task.task_id == task_id,
                Document.user_id == user_id
            ).with_for_update()
            task = (await db.execute(stmt_task)).scalars().first()
            if not task:
                return {"error": f"Aufgabe '{task_id}' nicht gefunden. Belohnung abgelehnt."}
            if task.is_rewarded:
                return {"error": f"Aufgabe '{task_id}' wurde bereits belohnt. Kein Cheating!"}

            task.is_rewarded = True
            await db.flush()
        else:
            # Guardrail 4: If no task_id, limit to max 10 coins for general good questions
            amount = min(amount, 10)

        stmt = select(User).where(User.user_id == user_id)
        current_user = (await db.execute(stmt)).scalars().first()
        if not current_user:
            return {"error": "Nutzer nicht gefunden"}
            
        now_utc = datetime.now(timezone.utc)
        stmt_boosts = select(ActiveItem).where(
            ActiveItem.user_id == user_id,
            (ActiveItem.expires_at == None) | (ActiveItem.expires_at > now_utc)
        )
        active_boosts = (await db.execute(stmt_boosts)).scalars().all()
        
        xp_multiplier = 1.0
        for boost in active_boosts:
            if "xp_multiplier" in boost.effects:
                xp_multiplier *= float(boost.effects["xp_multiplier"])
                
        final_exp = int(amount * xp_multiplier)
        current_user.coins += amount
        current_user.experience += final_exp
        
        await db.commit()
        
    await manager.send_personal_message(user_id, {
        "type": "REWARD_GAINED",
        "coins": amount,
        "experience": final_exp,
        "total_experience": current_user.experience,
        "reason": reason
    })
        
    return {
        "coins_awarded": amount, 
        "exp_awarded": final_exp, 
        "reason": reason
    }

register(ToolDefinition(
    name="award_coins_and_exp",
    description="Vergibt virtuelle Münzen und Erfahrungspunkte an den Nutzer als Belohnung für eine gute Antwort. Wenn sich die Antwort auf eine bestimmte Aufgabe bezieht, gib die task_id an.",
    parameters={
        "type": "object",
        "properties": {
            "amount": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Basis-Menge an Münzen/Exp (Max 100)"},
            "reason": {"type": "string", "description": "Grund für die Belohnung"},
            "task_id": {"type": "string", "description": "Optionale ID der gelösten Aufgabe zur Verifizierung"}
        },
        "required": ["amount", "reason"],
    },
    fn=_award_coins_and_exp,
))

# ─── add_calendar_note ────────────────────────────────────────────────────────
async def _add_calendar_note(title: str, content: str, start_time: str, end_time: str) -> ToolResult:
    """Real: Trägt eine Notiz/Lerneinheit in den Kalender ein."""
    user_id = current_user_id.get()
    if not user_id:
        return {"error": "Kein user_id im Kontext"}
        
    log.info("add_calendar_note called", extra={"user_id": user_id, "title": title})
    
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except ValueError as e:
        return {"error": f"Ungültiges Datumsformat: {e}"}

    async with AsyncSessionLocal() as db:
        note = CalendarNote(
            note_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            content=content,
            start_time=start_dt,
            end_time=end_dt,
            created_at=datetime.now(timezone.utc)
        )
        db.add(note)
        await db.commit()
        
    return {"status": "success", "title": title, "start_time": start_time}

register(ToolDefinition(
    name="add_calendar_note",
    description="Erstellt einen Kalendereintrag (Lernsession/Erinnerung) für den Nutzer.",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Kurzer Titel des Termins"},
            "content": {"type": "string", "description": "Details oder Ziele der Lernsession"},
            "start_time": {"type": "string", "description": "Startzeitpunkt als ISO-8601 String (z.B. 2026-06-30T15:00:00Z)"},
            "end_time": {"type": "string", "description": "Endzeitpunkt als ISO-8601 String"}
        },
        "required": ["title", "content", "start_time", "end_time"],
    },
    fn=_add_calendar_note,
))
