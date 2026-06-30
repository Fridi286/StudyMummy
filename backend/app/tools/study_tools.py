"""
StudyMummy Agent-Tools.

Jedes Tool ist eine async-Funktion mit klarer Signatur.
Mock-Implementierungen können durch echte Services ersetzt werden
(Hinweis Übungsblatt 03: „Fangt mit Mock-Tools an!").
"""
import json
from datetime import datetime, timezone
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.models import LearningProfile as DbLearningProfile
from app.db.session import AsyncSessionLocal
from app.services.session_service import update_profile
from app.tools.registry import ToolDefinition, register, ToolResult
from app.core.logging import get_logger

log = get_logger(__name__)

settings = get_settings()


def _clamp_score(score: float) -> float:
    return round(min(1.0, max(0.0, score)), 2)


def _normalize_verdict(value: str) -> str:
    value = value.strip().lower().replace("-", "_").replace(" ", "_")
    if value in {"correct", "korrekt", "richtig"}:
        return "correct"
    if value in {"partially_correct", "partial", "teilweise_korrekt", "teilweise"}:
        return "partially_correct"
    return "incorrect"


def _hint_for_level(verdict: str, expected_concept: str, detected_error: str, help_level: int) -> str:
    level = min(4, max(1, help_level))
    if verdict == "correct":
        return "Gut gemacht. Erklaere kurz, warum dein Schritt funktioniert."
    if level == 1:
        return f"Schau noch einmal auf das zentrale Konzept: {expected_concept}."
    if level == 2:
        return f"Pruefe gezielt, wie {expected_concept} in deiner Antwort vorkommt."
    if level == 3:
        return f"Gehe Schritt fuer Schritt vor: notiere zuerst {expected_concept}, wende es dann auf die Aufgabe an."
    return (
        f"Ausfuehrlicher Hinweis: Deine Antwort passt noch nicht ganz zu {expected_concept}. "
        f"Korrigiere zuerst diesen Punkt: {detected_error or 'das zentrale Konzept fehlt oder ist unklar'}."
    )


def _fallback_evaluation(user_answer: str, expected_concept: str, help_level: int) -> dict[str, Any]:
    answer = user_answer.strip().lower()
    concept = expected_concept.strip().lower()
    has_concept = bool(concept and concept in answer)
    has_substantial_answer = len(answer.split()) >= 4

    if has_concept:
        verdict = "correct"
        score = 1.0
        detected_error = ""
    elif has_substantial_answer:
        verdict = "partially_correct"
        score = 0.5
        detected_error = f"Das erwartete Konzept '{expected_concept}' wird noch nicht klar genutzt."
    else:
        verdict = "incorrect"
        score = 0.0
        detected_error = "Die Antwort ist zu kurz oder bleibt zu unkonkret."

    return {
        "verdict": verdict,
        "is_correct": verdict == "correct",
        "score": score,
        "detected_error": detected_error,
        "next_hint": _hint_for_level(verdict, expected_concept, detected_error, help_level),
        "confidence_update": score,
    }


def _can_evaluate_locally(user_answer: str, expected_concept: str) -> bool:
    answer = user_answer.strip().lower()
    concept = expected_concept.strip().lower()
    stuck_markers = ("weiss nicht", "weiß nicht", "keine ahnung", "verstehe nicht")
    return bool(concept and concept in answer) or len(answer.split()) < 4 or any(marker in answer for marker in stuck_markers)


async def _llm_evaluate_answer(
    task_id: str,
    user_answer: str,
    expected_concept: str,
    help_level: int,
) -> dict[str, Any] | None:
    if settings.openai_api_key == "MISSING_KEY":
        return None

    client_kwargs: dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "timeout": settings.openai_timeout_seconds,
        "max_retries": settings.openai_max_retries,
    }
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url

    client = AsyncOpenAI(**client_kwargs)
    prompt = f"""Bewerte die Nutzerantwort fuer einen sokratischen Tutor.
Antworte ausschliesslich als JSON-Objekt mit diesen Feldern:
- verdict: "correct", "partially_correct" oder "incorrect"
- detected_error: kurzer erkannter Fehler oder leerer String
- next_hint: naechster Hinweis passend zu Hilfestufe {help_level}
- confidence_update: Zahl zwischen 0.0 und 1.0

Hilfestufen:
1 = kleiner Denkanstoss, 2 = konkreter Hinweis, 3 = Schritt-fuer-Schritt, 4 = ausfuehrliche Loesung.

task_id: {task_id}
expected_concept: {expected_concept}
user_answer: {user_answer}
"""
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
    except Exception as e:
        log.warning(f"LLM answer evaluation failed; using fallback: {e}")
        return None

    verdict = _normalize_verdict(str(parsed.get("verdict", "")))
    detected_error = str(parsed.get("detected_error", "") or "")
    confidence_update = _clamp_score(float(parsed.get("confidence_update", 0.0) or 0.0))
    next_hint = str(parsed.get("next_hint", "") or "").strip()
    if not next_hint:
        next_hint = _hint_for_level(verdict, expected_concept, detected_error, help_level)

    return {
        "verdict": verdict,
        "is_correct": verdict == "correct",
        "score": confidence_update,
        "detected_error": detected_error,
        "next_hint": next_hint,
        "confidence_update": confidence_update,
    }


# ─── evaluate_answer ──────────────────────────────────────────────────────────
async def _evaluate_answer(
    task_id: str,
    user_answer: str,
    expected_concept: str,
    help_level: int = 1,
) -> ToolResult:
    """Bewertet Nutzerantwort strukturiert; nutzt LLM mit robustem Fallback."""
    log.info("evaluate_answer called", extra={"task_id": task_id})
    evaluation = None
    if not _can_evaluate_locally(user_answer, expected_concept):
        evaluation = await _llm_evaluate_answer(task_id, user_answer, expected_concept, help_level)
    if evaluation is None:
        evaluation = _fallback_evaluation(user_answer, expected_concept, help_level)

    return {
        "task_id": task_id,
        "verdict": evaluation["verdict"],
        "is_correct": evaluation["is_correct"],
        "feedback": evaluation["next_hint"],
        "detected_error": evaluation["detected_error"],
        "next_hint": evaluation["next_hint"],
        "confidence_update": evaluation["confidence_update"],
        "score": evaluation["score"],
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
            "help_level": {"type": "integer", "minimum": 1, "maximum": 4, "description": "Hilfestufe 1-4"},
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
    error_pattern: str = "",
) -> ToolResult:
    """Aktualisiert Confidence-Wert und Fehlerpattern persistent."""
    log.info("update_learning_profile called", extra={"user_id": user_id})
    clamped_score = _clamp_score(score)
    persisted = False
    error_patterns: list[str] = []

    try:
        async with AsyncSessionLocal() as db:
            profile = await update_profile(db, user_id, tag, clamped_score)
            error_patterns = list(profile.error_patterns)

            cleaned_error = error_pattern.strip()
            if cleaned_error and cleaned_error not in error_patterns:
                error_patterns.append(cleaned_error)
                await db.execute(
                    update(DbLearningProfile)
                    .where(DbLearningProfile.user_id == user_id)
                    .values(
                        error_patterns=error_patterns,
                        last_seen=datetime.now(timezone.utc),
                    )
                )
                await db.commit()
            else:
                result = await db.execute(select(DbLearningProfile).where(DbLearningProfile.user_id == user_id))
                db_profile = result.scalars().first()
                if db_profile:
                    error_patterns = db_profile.error_patterns or []
            persisted = True
    except Exception as e:
        log.warning(f"Persistent learning profile update failed: {e}")

    return {
        "user_id": user_id,
        "tag": tag,
        "new_confidence": clamped_score,
        "error_patterns": error_patterns,
        "updated": persisted,
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
            "error_pattern": {"type": "string", "description": "Optional erkanntes Fehlerpattern."},
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


# ─── award_coins ──────────────────────────────────────────────────────────────
async def _award_coins(user_id: str, amount: int, reason: str) -> ToolResult:
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
