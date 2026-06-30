"""
LLM service for chat, tool use, and task extraction.
"""
import json
import time
from typing import Any, Iterable, cast

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionContentPartParam,
    ChatCompletionMessageParam,
)

from app.core.config import get_settings
from app.core.logging import get_logger, get_trace_id
from app.models.agent import ExtractedTask
from app.tools.registry import as_openai_tools, get

log = get_logger(__name__)

SOCRATIC_SYSTEM_PROMPT = """Du bist StudyMummy, ein sokratischer Tutor-Agent.
Deine Aufgabe ist es, Lernende durch gezielte Rueckfragen zum Verstaendnis zu fuehren.
Gib niemals direkt die Loesung, wenn der Nutzer noch nicht nachgedacht hat.

Prinzipien:
1. Stelle immer eine Rueckfrage, bevor du erklaerst.
2. Passe dein Hilfeniveau dynamisch an.
3. Anerkenne Fortschritte und vergib Muenzen bei korrekten Antworten.
4. Wenn eine Aufgabe geloest ist, aktualisiere das Lernprofil.
5. Antworte immer auf Deutsch, klar und motivierend.

Hilfestufen:
Level 1 = kleiner Denkanstoss, keine Loesung.
Level 2 = konkreter Hinweis auf den naechsten Schritt.
Level 3 = Schritt-fuer-Schritt-Anleitung, aber mit aktiver Rueckfrage.
Level 4 = ausfuehrliche Loesung mit Erklaerung, wenn der Nutzer sie klar braucht.

Wenn du Nutzerantworten bewertest, nutze evaluate_answer mit task_id, user_answer,
expected_concept und help_level. Nutze danach update_learning_profile mit user_id,
tag, score und optional error_pattern."""


def build_tutor_system_prompt(
    help_level: int = 1,
    user_id: str | None = None,
    task_id: str | None = None,
) -> str:
    bounded_level = min(4, max(1, help_level))
    level_guidance = {
        1: "Gib nur einen kleinen Denkanstoss und stelle eine Rueckfrage.",
        2: "Gib einen konkreten Hinweis auf den naechsten sinnvollen Schritt.",
        3: "Fuehre Schritt fuer Schritt, lasse den Nutzer aber Zwischenschritte selbst nennen.",
        4: "Gib eine ausfuehrliche Loesung mit Begruendung und markiere typische Fehler.",
    }[bounded_level]
    context_lines = [
        SOCRATIC_SYSTEM_PROMPT,
        "",
        f"Aktuelle Hilfestufe: Level {bounded_level}. {level_guidance}",
    ]
    if user_id:
        context_lines.append(f"Aktueller user_id fuer Lernprofil-Tools: {user_id}")
    if task_id:
        context_lines.append(f"Aktuelle task_id: {task_id}")
    return "\n".join(context_lines)


def _preview(value: str | Iterable[ChatCompletionContentPartParam], max_chars: int = 180) -> str:
    text = str(value).replace("\n", " ").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _last_user_message(messages: list[ChatCompletionMessageParam]) -> str:
    for message in reversed(messages):
        if message["role"] == "user":
            return _preview(message.get("content", ""))
    return ""


class LLMService:
    def __init__(self):
        settings = get_settings()
        client_kwargs: dict[str, Any] = {
            "api_key": settings.openai_api_key,
            "timeout": settings.openai_timeout_seconds,
            "max_retries": settings.openai_max_retries,
        }
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        self.client = AsyncOpenAI(**client_kwargs)
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature

    async def chat_with_tools(
        self,
        messages: list[ChatCompletionMessageParam],
        system_prompt: str = SOCRATIC_SYSTEM_PROMPT,
        extra_context: str | None = None,
    ) -> tuple[str, list[str]]:
        """
        Run one or more LLM calls with optional tool use.
        """
        trace = get_trace_id()
        started_at = time.perf_counter()
        log.info(
            f"[{trace}] LLM call started, messages={len(messages)}, "
            f"extra_context={bool(extra_context)}, input_preview={_last_user_message(messages)!r}"
        )

        full_messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]
        if extra_context:
            full_messages.append({
                "role": "system",
                "content": f"[RAG-Kontext]\n{extra_context}",
            })
        full_messages.extend(messages)

        tools = as_openai_tools()
        supports_tools = "qwen" not in self.model.lower()
        tool_calls_made: list[str] = []

        for _ in range(5):
            call_started_at = time.perf_counter()
            try:
                if tools and supports_tools:
                    log.info(f"[{trace}] LLM call with model={self.model!r}, tool_choice='auto'")
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        temperature=self.temperature,
                        messages=full_messages,
                        tools=tools,
                        tool_choice="auto",
                    )
                else:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        temperature=self.temperature,
                        messages=full_messages,
                    )
            except Exception as e:
                return self._llm_error_response(e, trace, started_at, tool_calls_made)

            choice = response.choices[0]
            assistant_msg = choice.message
            call_duration_ms = round((time.perf_counter() - call_started_at) * 1000, 1)
            response_preview = _preview(assistant_msg.content or "")
            log.info(
                f"[{trace}] LLM response received in {call_duration_ms}ms, "
                f"tool_calls={len(assistant_msg.tool_calls or [])}, "
                f"response_preview={response_preview!r}"
            )

            msg_dict = cast(ChatCompletionMessageParam, cast(Any, assistant_msg.model_dump(exclude_none=True)))
            full_messages.append(msg_dict)

            if not assistant_msg.tool_calls:
                duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
                log.info(
                    f"[{trace}] LLM finished after {duration_ms}ms, "
                    f"tools_called={tool_calls_made}, final_preview={response_preview!r}"
                )
                return assistant_msg.content or "", tool_calls_made

            for tc in assistant_msg.tool_calls:
                if tc.type != "function":
                    continue

                fn_name = tc.function.name
                tool_calls_made.append(fn_name)
                try:
                    fn_args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError as e:
                    result = {"error": f"Invalid tool arguments: {e.msg}"}
                    log.error(f"[{trace}] Tool argument JSON error for {fn_name}: {e}")
                    full_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
                    continue

                log.info(f"[{trace}] Tool call: {fn_name}({fn_args})")

                try:
                    tool_def = get(fn_name)
                    result = await tool_def.fn(**fn_args)
                except KeyError as e:
                    result = {"error": str(e)}
                except Exception as e:
                    log.error(f"[{trace}] Tool error: {e}")
                    result = {"error": str(e)}

                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
        log.warning(f"[{trace}] LLM max steps reached after {duration_ms}ms")
        return "Maximale Schrittanzahl erreicht.", tool_calls_made

    def _llm_error_response(
        self,
        error: Exception,
        trace: str,
        started_at: float,
        tool_calls_made: list[str],
    ) -> tuple[str, list[str]]:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
        log.error(f"[{trace}] LLM API error after {duration_ms}ms: {error}")
        error_text = str(error)
        if "Model Group" in error_text or "litellm" in error_text.lower():
            return (
                "Der HAW-LLM-Endpunkt ist gerade nicht verfuegbar oder das Modell "
                f"{self.model!r} ist dort momentan nicht erreichbar. Bitte pruefe eduVPN "
                "und versuche es gleich erneut.",
                tool_calls_made,
            )
        return (
            "Ich kann gerade keine zuverlaessige KI-Antwort erzeugen. "
            "Bitte versuche es gleich noch einmal oder formuliere die Frage etwas kuerzer.",
            tool_calls_made,
        )

    async def extract_tasks_from_text(self, text: str) -> list[ExtractedTask]:
        """
        Extract structured tasks from uploaded text/PDF/OCR text.
        """
        trace = get_trace_id()
        started_at = time.perf_counter()
        log.info(f"[{trace}] Task extraction started, input_preview={_preview(text)!r}")

        prompt = f"""Analysiere den folgenden Text und extrahiere alle Lernaufgaben.
Gib das Ergebnis als JSON-Array zurueck. Jede Aufgabe hat:
- task_id (string, eindeutig, z.B. "task_01")
- tags (array of strings, z.B. ["Mathematik", "Lineare Funktionen"])
- difficulty (integer, 1-5)
- task_text (string)
- required_concepts (array of strings)
- status: immer "open"

TEXT:
{text[:4000]}

JSON:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
        except Exception as e:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
            log.error(f"[{trace}] Task extraction API error after {duration_ms}ms: {e}")
            return []

        content = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            log.error(f"[{trace}] Task extraction JSON error: {e}")
            return []

        tasks = parsed.get("tasks", parsed) if isinstance(parsed, dict) else parsed
        if not isinstance(tasks, list):
            tasks = []

        duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
        log.info(
            f"[{trace}] Extracted {len(tasks)} tasks after {duration_ms}ms, "
            f"response_preview={_preview(content)!r}"
        )
        return tasks
