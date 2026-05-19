"""
LLM-Service: kapselt alle OpenAI-Calls mit Tool Use (Function Calling).
Zentrale Stelle für alle LLM-Interaktionen – leicht gegen ein anderes LLM austauschbar.
"""
import json
from typing import Any, Optional
from openai import AsyncOpenAI
from app.core.config import get_settings
from app.core.logging import get_logger, get_trace_id
from app.tools.registry import get_all, get, as_openai_tools

log = get_logger(__name__)

SOCRATIC_SYSTEM_PROMPT = """Du bist StudyMummy, ein sokratischer Tutor-Agent.
Deine Aufgabe ist es, Lernende durch gezielte Rückfragen zum Verständnis zu führen – 
gib NIEMALS direkt die Lösung, wenn der Nutzer noch nicht nachgedacht hat.

Prinzipien:
1. Stelle immer eine Rückfrage, bevor du erklärst.
2. Passe dein Hilfeniveau dynamisch an (Level 1: Hinweis, Level 2: Teilanleitung, Level 3: Musterlösung).
3. Anerkenne Fortschritte und vergibt Münzen bei korrekten Antworten.
4. Wenn eine Aufgabe gelöst ist, aktualisiere das Lernprofil.
5. Antworte immer auf Deutsch, klar und motivierend."""


class LLMService:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature

    async def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = SOCRATIC_SYSTEM_PROMPT,
        extra_context: Optional[str] = None,
    ) -> tuple[str, list[str]]:
        """
        Führt einen LLM-Call mit Tool Use durch (ReAct-Loop).
        Gibt (final_message, tool_calls_made) zurück.
        """
        trace = get_trace_id()
        log.info(f"[{trace}] LLM call started, messages={len(messages)}")

        full_messages = [{"role": "system", "content": system_prompt}]
        if extra_context:
            full_messages.append({
                "role": "system",
                "content": f"[RAG-Kontext]\n{extra_context}"
            })
        full_messages.extend(messages)

        tools = as_openai_tools()
        tool_calls_made: list[str] = []

        # ReAct-Loop: Thought → Action → Observation
        for _ in range(5):  # max 5 Iterationen als Guardrail
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=full_messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
            )

            choice = response.choices[0]
            assistant_msg = choice.message

            full_messages.append(assistant_msg.model_dump(exclude_none=True))

            if not assistant_msg.tool_calls:
                log.info(f"[{trace}] LLM finished, tools_called={tool_calls_made}")
                return assistant_msg.content or "", tool_calls_made

            # Tool-Calls ausführen (Observation)
            for tc in assistant_msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                tool_calls_made.append(fn_name)
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

        return "Maximale Schrittanzahl erreicht.", tool_calls_made

    async def extract_tasks_from_text(self, text: str) -> list[dict[str, Any]]:
        """
        Perception-Schicht: Extrahiert strukturierte Aufgaben aus Freitext (PDF/OCR).
        Verwendet Structured Output via JSON Schema.
        """
        trace = get_trace_id()
        log.info(f"[{trace}] Task extraction started")

        prompt = f"""Analysiere den folgenden Text und extrahiere alle Lernaufgaben.
Gib das Ergebnis als JSON-Array zurück. Jede Aufgabe hat:
- task_id (string, eindeutig, z.B. "task_01")
- subject (string, z.B. "Mathematik")
- topic (string, z.B. "Lineare Funktionen")
- difficulty (integer, 1-5)
- task_text (string)
- required_concepts (array of strings)
- status: immer "open"

TEXT:
{text[:4000]}

JSON:"""

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        tasks = parsed.get("tasks", parsed) if isinstance(parsed, dict) else parsed
        if not isinstance(tasks, list):
            tasks = []
        log.info(f"[{trace}] Extracted {len(tasks)} tasks")
        return tasks
