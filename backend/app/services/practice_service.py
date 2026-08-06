import uuid
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
log = get_logger(__name__)

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

PRACTICE_REWARD_COINS = 5


class GeneratedPracticeTask(BaseModel):
    task_type: Literal["text", "multiple_choice"] = Field(description="Aufgabentyp: text oder multiple_choice.")
    context_excerpt: str = Field(
        default="",
        description="Sichtbare Grundlagen für die neue Aufgabe: relevante Definitionen, Formeln, Daten oder kurze Erklärungen, nicht die Originalaufgabe aus dem Dokument.",
    )
    question: str = Field(description="Eine konkrete Lernaufgabe auf Deutsch, ohne Musterlösung.")
    options: list[str] = Field(default_factory=list, description="Bei multiple_choice genau 4 plausible Antwortoptionen, sonst leer.")
    correct_answer: str = Field(default="", description="Bei multiple_choice exakt die richtige Option aus options, sonst leer.")
    reference_answer: str = Field(description="Eine kurze Musterantwort oder Lösungsskizze.")
    explanation: str = Field(description="Feedback-Hinweise, worauf eine gute Antwort achten sollte.")
    key_concepts: list[str] = Field(default_factory=list)


class PracticeEvaluation(BaseModel):
    correct: bool = Field(description="Ob die Antwort inhaltlich ausreichend ist.")
    feedback: str = Field(description="Kurzes hilfreiches Feedback auf Deutsch.")


@dataclass
class PracticeTaskState:
    practice_task_id: str
    user_id: str
    task_type: Literal["text", "multiple_choice"]
    context_excerpt: str
    question: str
    options: list[str]
    correct_answer: str
    reference_answer: str
    explanation: str
    key_concepts: list[str]
    difficulty: int
    source_document_ids: list[str]
    awarded: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


_practice_tasks: dict[str, PracticeTaskState] = {}


def _compact_context(context: str, max_chars: int = 7000) -> str:
    compact = " ".join(context.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3] + "..."


def _difficulty_profile(difficulty: int) -> str:
    profiles = {
        1: (
            "Level 1: sehr einfach. Eine Basisidee, Erkennen/Zuordnen/kurze Definition, "
            "höchstens ein Denkschritt, sehr klare Hinweise in der Aufgabenstellung."
        ),
        2: (
            "Level 2: einfach. Eine direkte Anwendung mit einem kleinen neu erfundenen Beispiel, "
            "ein bis zwei Schritte, keine versteckten Fallen."
        ),
        3: (
            "Level 3: mittel. Zwei bis drei Schritte, Transfer auf ein neues Beispiel, "
            "mindestens zwei Konzepte aus dem Themenfeld müssen verbunden werden."
        ),
        4: (
            "Level 4: schwer. Mehrschrittige Anwendung mit Begründung, plausible Ablenkungen "
            "oder Randfälle, der Nutzer muss Unterschiede zwischen Konzepten erklären."
        ),
        5: (
            "Level 5: sehr schwer. Prüfungsnaher Transfer mit neuem Szenario, mehreren Bedingungen, "
            "Abwägung/Begründung und mindestens einem nicht offensichtlichen Zwischenschritt."
        ),
    }
    return profiles.get(difficulty, profiles[3])


def _fallback_task(
    *,
    context: str,
    difficulty: int,
    tags: list[str],
    source_document_ids: list[str],
    user_id: str,
) -> PracticeTaskState:
    topic = ", ".join(tags[:3]) if tags else "dem ausgewählten Themenfeld"
    foundation = _compact_context(context, 360)
    task_type: Literal["text", "multiple_choice"] = "multiple_choice" if random.random() < 0.45 else "text"
    options: list[str] = []
    correct_answer = ""
    context_excerpt = (
        f"Themenfeld: {topic}.\n"
        f"Schwierigkeitsprofil: {_difficulty_profile(difficulty)}"
    )
    if foundation:
        context_excerpt += f"\nRelevante Grundlage aus dem Material: {foundation}"

    if task_type == "multiple_choice":
        if difficulty <= 2:
            question = f"Welche Aussage beschreibt das Grundprinzip von {topic} am besten?"
            options = [
                "Das zentrale Konzept wird korrekt benannt und direkt angewendet.",
                "Alle Begriffe aus dem Themenfeld bedeuten immer dasselbe.",
                "Eine Lösung ist nur richtig, wenn keine Begründung angegeben wird.",
                "Beispiele ersetzen die Definition vollständig.",
            ]
        elif difficulty <= 4:
            question = (
                f"Eine neue Lernsituation zu {topic} soll gelöst werden. Welche Vorgehensweise ist fachlich am sinnvollsten?"
            )
            options = [
                "Zuerst die relevanten Begriffe klären, dann die passenden Regeln schrittweise anwenden und das Ergebnis begründen.",
                "Direkt ein Ergebnis raten und erst danach prüfen, ob die Begriffe dazu passen.",
                "Nur das auffälligste Stichwort verwenden und alle Randbedingungen ignorieren.",
                "Die Aufgabe in eine bekannte Musterlösung umbenennen, ohne die neue Situation zu prüfen.",
            ]
        else:
            question = (
                f"In einer anspruchsvollen Transferaufgabe zu {topic} treten mehrere Bedingungen gleichzeitig auf. "
                "Welche Strategie vermeidet am ehesten einen fachlichen Fehlschluss?"
            )
            options = [
                "Die Bedingungen getrennt prüfen, Beziehungen zwischen den Konzepten begründen und erst dann eine Schlussfolgerung ziehen.",
                "Die komplexeste Formel auswählen, auch wenn ihre Voraussetzungen nicht geprüft wurden.",
                "Nur den ersten passenden Begriff verwenden, weil weitere Bedingungen meist redundant sind.",
                "Die Antwort auf eine Definition reduzieren und alle Gegenbeispiele ausblenden.",
            ]
        correct_answer = options[0]
    elif difficulty <= 2:
        question = (
            f"Neue Übungsaufgabe zu {topic}: Erkläre einen zentralen Begriff in eigenen Worten "
            "und bilde dazu ein kurzes eigenes Beispiel."
        )
    elif difficulty <= 4:
        question = (
            f"Neue Übungsaufgabe zu {topic}: Entwickle eine Lösungsskizze für ein eigenes Beispiel, "
            "in dem zwei Konzepte aus dem Themenfeld zusammenwirken. Begründe jeden Schritt."
        )
    else:
        question = (
            f"Neue Prüfungsaufgabe zu {topic}: Entwirf ein komplexes Szenario mit mehreren Bedingungen, "
            "analysiere mögliche Fehlerquellen und leite eine begründete Schlussfolgerung ab."
        )

    task_id = str(uuid.uuid4())
    return PracticeTaskState(
        practice_task_id=task_id,
        user_id=user_id,
        task_type=task_type,
        context_excerpt=context_excerpt,
        question=question,
        options=options,
        correct_answer=correct_answer,
        reference_answer=(
            "Eine gute Antwort greift die relevanten Begriffe aus dem gefilterten Material auf, "
            "ordnet sie fachlich korrekt ein und begründet die einzelnen Schritte nachvollziehbar."
        ),
        explanation="Achte auf klare Begriffe, nachvollziehbare Begründungen und ein eigenes Beispiel.",
        key_concepts=tags[:5] or ["gefiltertes Material", "Begründung", "Anwendung"],
        difficulty=difficulty,
        source_document_ids=source_document_ids,
    )


async def create_practice_task(
    *,
    context: str,
    difficulty: int,
    tags: list[str],
    text_filter: str,
    source_document_ids: list[str],
    user_id: str,
) -> PracticeTaskState:
    compact_context = _compact_context(context)
    tag_hint = ", ".join(tags) if tags else "keine expliziten Tag-Filter"
    search_hint = text_filter.strip() or "kein Textfilter"
    task_type: Literal["text", "multiple_choice"] = "multiple_choice" if random.random() < 0.45 else "text"
    difficulty_profile = _difficulty_profile(difficulty)
    variation_seed = str(uuid.uuid4())[:8]

    try:
        completion = await client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du bist ein deutscher Tutor-Agent für einen Practice-Modus. "
                        "Nutze den bereitgestellten Dokumentinhalt NUR als Themen- und Konzeptquelle. "
                        "Extrahiere, kopiere oder paraphrasiere keine Aufgaben aus dem Dokument. "
                        "Wenn der Dokumentinhalt Übungsaufgaben enthält, ignoriere deren konkrete Aufgabenstellung, "
                        "Zahlen, Namen und Szenarien. Erzeuge stattdessen eine neue, originale Aufgabe zum selben Themenfeld "
                        "mit neuen Zahlen, neuen Beispielen oder einem neuen Szenario. "
                        "Die Aufgabe muss vollständig ohne ein externes Quelldokument lösbar sein. "
                        "context_excerpt soll nur die sichtbaren Grundlagen enthalten, die zum Lösen nötig sind "
                        "(Definitionen, Regeln, Formeln, kurze fachliche Erinnerung), aber keine Originalaufgabe. "
                        "Die Frage darf nicht lauten 'beziehe dich auf den Text/das Blatt/die vorige Aufgabe'. "
                        "Die Frage selbst muss klar machen, was zu tun ist. "
                        "Wenn task_type multiple_choice ist, erzeuge genau 4 Optionen und setze correct_answer "
                        "exakt auf eine dieser Optionen. Bei höherer Schwierigkeit müssen die Distraktoren plausibler "
                        "und näher an typischen Fehlkonzepten liegen."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Variations-ID für eine neue, nicht wiederholte Aufgabe: {variation_seed}\n"
                        f"Gewünschter Aufgabentyp: {task_type}\n"
                        f"Schwierigkeit: {difficulty}/5\n"
                        f"Schwierigkeitsprofil: {difficulty_profile}\n"
                        f"Tag-Filter: {tag_hint}\n"
                        f"Textfilter: {search_hint}\n\n"
                        f"Themenquelle aus ausgewählten Dokumenten:\n{compact_context}"
                    ),
                },
            ],
            response_format=GeneratedPracticeTask,
        )
        parsed = completion.choices[0].message.parsed
        if not parsed:
            raise ValueError("No parsed practice task returned")

        parsed_options = [option.strip() for option in parsed.options if option.strip()]
        if task_type == "multiple_choice":
            if len(parsed_options) != 4:
                raise ValueError("Multiple choice task did not include exactly 4 options")
            if parsed.correct_answer.strip() not in parsed_options:
                raise ValueError("Multiple choice correct_answer is not one of the options")
        else:
            parsed_options = []

        task_id = str(uuid.uuid4())
        state = PracticeTaskState(
            practice_task_id=task_id,
            user_id=user_id,
            task_type=task_type,
            context_excerpt=parsed.context_excerpt.strip() or (
                f"Themenfeld aus den ausgewählten Dokumenten.\nSchwierigkeitsprofil: {difficulty_profile}"
            ),
            question=parsed.question.strip(),
            options=parsed_options,
            correct_answer=parsed.correct_answer.strip() if task_type == "multiple_choice" else "",
            reference_answer=parsed.reference_answer.strip(),
            explanation=parsed.explanation.strip(),
            key_concepts=[c.strip() for c in parsed.key_concepts if c.strip()],
            difficulty=difficulty,
            source_document_ids=source_document_ids,
        )
    except Exception as e:
        log.warning(f"Practice task generation failed, using fallback: {e}")
        state = _fallback_task(
            context=context,
            difficulty=difficulty,
            tags=tags,
            source_document_ids=source_document_ids,
            user_id=user_id,
        )

    _practice_tasks[state.practice_task_id] = state
    return state


def get_practice_task(practice_task_id: str, user_id: str) -> PracticeTaskState | None:
    state = _practice_tasks.get(practice_task_id)
    if not state or state.user_id != user_id:
        return None
    return state


async def evaluate_practice_answer(state: PracticeTaskState, answer: str) -> PracticeEvaluation:
    answer_text = answer.strip()
    if not answer_text:
        return PracticeEvaluation(correct=False, feedback="Schreibe zuerst eine kurze Antwort, dann kann ich sie bewerten.")

    if state.task_type == "multiple_choice":
        if answer_text == state.correct_answer:
            return PracticeEvaluation(
                correct=True,
                feedback=f"Richtig. {state.explanation or 'Die ausgewählte Option passt zum Dokumentkontext.'}",
            )
        return PracticeEvaluation(
            correct=False,
            feedback="Das ist noch nicht die richtige Option. Schau dir die Begriffe in der Frage noch einmal genau an und versuche es erneut.",
        )

    try:
        completion = await client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du bewertest eine Lernantwort kurz und konstruktiv auf Deutsch. "
                        "Belohne Teilverständnis, korrigiere klare Fehler und stelle am Ende maximal eine kurze Vertiefungsfrage. "
                        "Bewerte passend zur Schwierigkeit: Bei Level 1-2 reicht eine einfache korrekte Kernaussage, "
                        "bei Level 3 braucht es Anwendung und Begründung, bei Level 4-5 braucht es mehrere Schritte, "
                        "saubere Fachbegriffe und eine nachvollziehbare Begründung."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Schwierigkeit: {state.difficulty}/5\n"
                        f"Schwierigkeitsprofil: {_difficulty_profile(state.difficulty)}\n\n"
                        f"Aufgabe:\n{state.question}\n\n"
                        f"Musterantwort:\n{state.reference_answer}\n\n"
                        f"Antwort des Nutzers:\n{answer_text}"
                    ),
                },
            ],
            response_format=PracticeEvaluation,
        )
        parsed = completion.choices[0].message.parsed
        if parsed:
            return parsed
    except Exception as e:
        log.warning(f"Practice answer evaluation failed, using fallback: {e}")

    min_lengths = {1: 12, 2: 24, 3: 50, 4: 90, 5: 130}
    min_length = min_lengths.get(state.difficulty, 50)
    has_reasoning = any(marker in answer_text.lower() for marker in ["weil", "daher", "deshalb", "begründ", "folg", "wenn", "also"])

    if len(answer_text) < min_length or (state.difficulty >= 3 and not has_reasoning):
        return PracticeEvaluation(
            correct=False,
            feedback=(
                "Das ist für diese Schwierigkeit noch nicht ausreichend. "
                "Ergänze eine klare Begründung, passende Fachbegriffe und mindestens einen nachvollziehbaren Zwischenschritt."
            ),
        )

    return PracticeEvaluation(
        correct=True,
        feedback=f"Gute Übungsantwort. Vergleiche deine Idee noch mit dieser Lösungsskizze: {state.reference_answer}",
    )
