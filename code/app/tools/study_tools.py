"""
StudyMummy Agent-Tools.

Jedes Tool ist eine async-Funktion mit klarer Signatur.
Mock-Implementierungen können durch echte Services ersetzt werden
(Hinweis Übungsblatt 03: „Fangt mit Mock-Tools an!").
"""
import json
from app.tools.registry import ToolDefinition, register
from app.core.logging import get_logger

log = get_logger(__name__)


# ─── evaluate_answer ──────────────────────────────────────────────────────────
async def _evaluate_answer(
    task_id: str,
    user_answer: str,
    expected_concept: str,
) -> dict:
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
    topic: str,
    score: float,
) -> dict:
    """Mock: aktualisiert Confidence-Wert eines Themas im Lernprofil."""
    log.info("update_learning_profile called", extra={"user_id": user_id})
    # TODO: echte DB-Persistenz
    return {
        "user_id": user_id,
        "topic": topic,
        "new_confidence": round(min(1.0, max(0.0, score)), 2),
        "updated": True,
    }

register(ToolDefinition(
    name="update_learning_profile",
    description="Speichert den neuen Confidence-Wert für ein Thema im Nutzerprofil.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "topic": {"type": "string"},
            "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": ["user_id", "topic", "score"],
    },
    fn=_update_learning_profile,
))


# ─── generate_quiz_questions ──────────────────────────────────────────────────
async def _generate_quiz_questions(
    topic: str,
    num_questions: int = 5,
    difficulty: int = 2,
) -> dict:
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
) -> dict:
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


# ─── award_coins ──────────────────────────────────────────────────────────────
async def _award_coins(user_id: str, amount: int, reason: str) -> dict:
    """Mock: vergibt virtuelle Währung (Gamification)."""
    log.info("award_coins called", extra={"user_id": user_id, "amount": amount})
    return {"user_id": user_id, "coins_awarded": amount, "reason": reason}

register(ToolDefinition(
    name="award_coins",
    description="Vergibt virtuelle Währung an den Nutzer als Belohnung.",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "amount": {"type": "integer", "minimum": 1},
            "reason": {"type": "string"},
        },
        "required": ["user_id", "amount", "reason"],
    },
    fn=_award_coins,
))
