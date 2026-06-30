"""
LLM-Service: kapselt alle OpenAI-Calls mit Tool Use (Function Calling).
Zentrale Stelle für alle LLM-Interaktionen – leicht gegen ein anderes LLM austauschbar.
"""
import json
import re
import time
import unicodedata
from typing import Iterable, cast, Any
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam, ChatCompletionContentPartParam
from app.core.config import get_settings
from app.core.logging import get_logger, get_trace_id
from app.tools.registry import get_all, get, as_openai_tools
from app.models.agent import ExtractedTask

log = get_logger(__name__)

SOCRATIC_SYSTEM_PROMPT = """Du bist StudyMummy, ein sokratischer Tutor-Agent.
Deine Aufgabe ist es, Lernende durch gezielte Rückfragen zum Verständnis zu führen – 
gib NIEMALS direkt die Lösung, wenn der Nutzer noch nicht nachgedacht hat.

Prinzipien:
1. Stelle immer eine Rückfrage, bevor du erklärst.
2. Passe dein Hilfeniveau dynamisch an (Level 1: Hinweis, Level 2: Teilanleitung, Level 3: Musterlösung).
3. Wenn der Nutzer eine gute Lösung oder kluge Frage einbringt (angemessen zur Schwierigkeit), belohne ihn mit dem Tool `award_coins_and_exp`!
4. Wenn der Nutzer eine Lerneinheit, Prüfung oder Deadline erwähnt, biete an oder trage es direkt als Termin mit dem Tool `add_calendar_note` ein.
5. Antworte immer auf Deutsch, klar und motivierend."""

MAX_USER_INPUT_CHARS = 4000
BLOCKED_INPUT_PATTERNS = (
    ("ignore_instructions", re.compile(r"(?i)\bignore\b.*\b(previous|all)\b.*\binstructions\b")),
    (
        "reveal_prompt",
        re.compile(r"(?i)\b(reveal|show|print)\b.*\b(system prompt|developer message|hidden prompt)\b"),
    ),
    ("developer_message", re.compile(r"(?i)\bdeveloper message\b")),
)


def _strip_invisible_chars(text: str) -> str:
    return "".join(
        char
        for char in text
        if unicodedata.category(char) not in {"Cc", "Cf"}
    )


def filter_user_input(text: str) -> str:
    cleaned = unicodedata.normalize("NFKC", text)
    cleaned = _strip_invisible_chars(cleaned.replace("\x00", ""))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > MAX_USER_INPUT_CHARS:
        raise ValueError("Eingabe ist zu lang.")
    for pattern_name, pattern in BLOCKED_INPUT_PATTERNS:
        if pattern.search(cleaned):
            log.warning("Blocked user input by filter", extra={"pattern": pattern_name})
            raise ValueError("Eingabe enthält unzulässige Anweisungen.")
    return cleaned


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
        if settings.openai_base_url:
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
        else:
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key
            )
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature

    async def chat_with_tools(
        self,
        messages: list[ChatCompletionMessageParam],
        system_prompt: str = SOCRATIC_SYSTEM_PROMPT,
        extra_context: str | None = None,
        allowed_tool_names: Iterable[str] | None = None,
    ) -> tuple[str, list[str]]:
        """
        Führt einen LLM-Call mit Tool Use durch (ReAct-Loop).
        Gibt (final_message, tool_calls_made) zurück.
        """
        filtered_messages: list[ChatCompletionMessageParam] = []
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "")
                if not isinstance(content, str):
                    content = str(content)
                filtered_content = filter_user_input(content)
                filtered_messages.append(cast(ChatCompletionMessageParam, {**message, "content": filtered_content}))
            else:
                filtered_messages.append(message)

        allowed_tool_set = set(allowed_tool_names) if allowed_tool_names is not None else None

        trace = get_trace_id()
        started_at = time.perf_counter()
        log.info(
            f"[{trace}] LLM call started, messages={len(messages)}, "
            f"extra_context={bool(extra_context)}, input_preview={_last_user_message(filtered_messages)!r}"
        )

        full_messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]
        if extra_context:
            full_messages.append({
                "role": "system",
                "content": f"[RAG-Kontext]\n{extra_context}"
            })
        if allowed_tool_names is not None:
            full_messages.append({
                "role": "system",
                "content": f"[Tool-Scope] Erlaubte Tools in diesem Kontext: {', '.join(allowed_tool_names)}. Nutze keine anderen Tools."
            })
        full_messages.extend(filtered_messages)

        tools = as_openai_tools(allowed_tool_names)
        supports_tools = "qwen" not in self.model.lower()
        tool_calls_made: list[str] = []

        # ReAct-Loop: Thought → Action → Observation
        for _ in range(5):  # max 5 Iterationen als Guardrail
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
                    duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
                    log.error(f"[{trace}] LLM API error after {duration_ms}ms: {e}")
                    return (
                    "Ich kann gerade keine zuverlässige KI-Antwort erzeugen. "
                    "Bitte versuche es gleich noch einmal oder formuliere die Frage etwas kürzer.",
                        tool_calls_made,
                    )

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

            # Tool-Calls ausführen (Observation)
            for tc in assistant_msg.tool_calls:
                if tc.type != "function":
                    continue
                fn_name = tc.function.name
                if allowed_tool_set is not None and fn_name not in allowed_tool_set:
                    log.warning(f"[{trace}] Blocked disallowed tool call: {fn_name}")
                    full_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({"error": "Tool not allowed in this context."}, ensure_ascii=False),
                    })
                    continue

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

    async def extract_tasks_from_text(self, text: str) -> list[ExtractedTask]:
        """
        Perception-Schicht: Extrahiert strukturierte Aufgaben aus Freitext (PDF/OCR).
        Verwendet Structured Output via JSON Schema.
        """
        trace = get_trace_id()
        started_at = time.perf_counter()
        log.info(f"[{trace}] Task extraction started, input_preview={_preview(text)!r}")

        prompt = f"""Analysiere den folgenden Text und extrahiere alle Lernaufgaben.
Gib das Ergebnis als JSON-Array zurück. Jede Aufgabe hat:
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
