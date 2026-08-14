import asyncio
from statistics import mean
from types import SimpleNamespace
from typing import Any, cast

from app.agents.orchestrator import AgentOrchestrator
from app.agents.protocol import AgentContext, AgentRunResult, ToolConversationResult
from app.core.logging import get_trace_id, trace_id_var
from app.evaluation.metrics import ChatRun, compare_trace_runs, evaluate_chat_run
from app.services.llm_service import LLMService
import app.tools.study_tools  # noqa: F401  # Register production tools for this standalone run.


INPUT_TEXT = "Ich verstehe die Nullstelle nicht."
EXPECTED_TOOLS = ("evaluate_answer",)


class FakeMessage:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        result = {"role": "assistant"}
        if self.content is not None:
            result["content"] = self.content
        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls
        return result


class FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)

    async def create(self, **kwargs):
        message = self.responses.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=FakeCompletions(responses))


class FakeMASLLM:
    """Deterministic specialist outputs; the MAS runtime itself remains production code."""

    def __init__(self):
        self.structured: list[dict[str, Any] | None] = [
            None,
            {
                "approved": False,
                "feedback": "Die Antwort nimmt die Lösung vorweg.",
                "requires_replan": False,
                "revised_response": "Stelle eine aktivierende Rückfrage.",
            },
            {"approved": True, "feedback": "Die Revision erfüllt den Plan."},
        ]
        self.drafts = [
            "Die Lösung ist x = -2.",
            "Was bedeutet der Schnittpunkt des Graphen mit der x-Achse?",
        ]

    async def complete_json(self, **_kwargs: Any) -> dict[str, Any] | None:
        return self.structured.pop(0)

    async def chat_with_tools(self, **_kwargs: Any) -> ToolConversationResult:
        return ToolConversationResult(response=self.drafts.pop(0))


def _tool_call(user_answer: str):
    return SimpleNamespace(
        id="call_evaluate_answer",
        type="function",
        function=SimpleNamespace(
            name="evaluate_answer",
            arguments=(
                '{"task_id":"task_01",'
                f'"user_answer":"{user_answer}",'
                '"expected_concept":"Nullstelle"}'
            ),
        ),
    )


def baseline_runs() -> list[ChatRun]:
    """Baseline: direct answers without StudyMummy's ReAct loop or tools."""
    return [
        ChatRun(
            variant="baseline_without_tools",
            input_text=INPUT_TEXT,
            response_text="Die Lösung ist x = -2.",
            trace_id="missing",
            tool_calls=(),
            expected_tools=EXPECTED_TOOLS,
        ),
        ChatRun(
            variant="baseline_without_tools",
            input_text=INPUT_TEXT,
            response_text="Du musst x = -2 einsetzen.",
            trace_id="",
            tool_calls=(),
            expected_tools=EXPECTED_TOOLS,
        ),
        ChatRun(
            variant="baseline_without_tools",
            input_text=INPUT_TEXT,
            response_text="Die Antwort lautet -2.",
            trace_id="bad",
            tool_calls=(),
            expected_tools=EXPECTED_TOOLS,
        ),
    ]


async def study_mummy_react_run(
    trace_id: str,
    user_answer: str,
    final_response: str,
) -> ChatRun:
    """
    Runs the real StudyMummy LLMService ReAct loop with a fake OpenAI client.

    The OpenAI model output is mocked, but the orchestration, tool dispatch,
    tool execution, tool observation handling, and trace collection use the
    production StudyMummy code path.
    """
    trace_id_var.set(trace_id)

    service = LLMService()
    service.client = FakeClient(
        responses=[
            FakeMessage(content=None, tool_calls=[_tool_call(user_answer)]),
            FakeMessage(content=final_response),
        ]
    )

    result = await service.chat_with_tools(
        messages=[{"role": "user", "content": INPUT_TEXT}]
    )

    return ChatRun(
        variant="react_with_tools_and_tracing",
        input_text=INPUT_TEXT,
        response_text=result.response,
        trace_id=get_trace_id(),
        tool_calls=tuple(result.successful_tool_names),
        expected_tools=EXPECTED_TOOLS,
    )


async def study_mummy_react_runs() -> list[ChatRun]:
    return [
        await study_mummy_react_run(
            trace_id="a3f9b1c2",
            user_answer="Ich weiß es nicht",
            final_response="Gute Frage: Was bedeutet es, wenn der Graph die x-Achse schneidet?",
        ),
        await study_mummy_react_run(
            trace_id="b4e8c2d1",
            user_answer="Vielleicht x = 2",
            final_response="Welche Stelle am Graphen würdest du zuerst betrachten?",
        ),
        await study_mummy_react_run(
            trace_id="c7d1e9a4",
            user_answer="Nullstelle",
            final_response="Lass uns Schritt für Schritt überlegen: Wo liegt der Schnittpunkt mit der x-Achse?",
        ),
    ]


async def study_mummy_mas_run() -> AgentRunResult:
    """Exercise message routing, critique, revision, and final acceptance."""
    llm = cast(LLMService, cast(object, FakeMASLLM()))
    return await AgentOrchestrator(llm).run(
        AgentContext(
            user_id="experiment_user",
            session_id="experiment_session",
            message=INPUT_TEXT,
            current_task_id="task_01",
            history=[{"role": "user", "content": INPUT_TEXT}],
            current_time="2026-08-14T12:00:00+00:00",
        )
    )


async def main() -> None:
    runs = baseline_runs() + await study_mummy_react_runs()
    rows = [evaluate_chat_run(run) for run in runs]
    variants = sorted({run.variant for run in runs})

    print("| Variante | Läufe | Ø Score | Tool Coverage | Qualitatives Ergebnis |")
    print("|---|---:|---:|---:|---|")
    for variant in variants:
        variant_rows = [row for row in rows if row["variant"] == variant]
        avg_score = mean(row["quantitative_score"] for row in variant_rows)
        avg_tool_coverage = mean(row["tool_coverage"] for row in variant_rows)
        labels = sorted({row["qualitative_label"] for row in variant_rows})
        print(
            f"| {variant} | {len(variant_rows)} | {avg_score:.2f} | "
            f"{avg_tool_coverage:.2f} | {', '.join(labels)} |"
        )

    react_runs = [run for run in runs if run.variant == "react_with_tools_and_tracing"]
    trace_comparison = compare_trace_runs(react_runs[:2])
    print()
    print("Trace comparison:", trace_comparison)

    mas_result = await study_mummy_mas_run()
    print()
    print(
        "MAS coordination:",
        {
            "agents": mas_result.agents_involved,
            "rounds": mas_result.coordination_rounds,
            "messages": [item.kind.value for item in mas_result.communications],
            "final_response": mas_result.response,
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
