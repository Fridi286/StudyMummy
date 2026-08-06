"""
Semantic evaluation helpers for repeatable agent-quality checks.

The functions are deterministic and intentionally small: they let us evaluate
mocked or recorded agent runs without depending on a live LLM.
"""
from dataclasses import dataclass
import re
from statistics import mean
from typing_extensions import TypedDict

class ChatRunMetrics(TypedDict):
    variant: str
    has_non_empty_response: bool
    has_trace_id: bool
    asks_or_guides: bool
    avoids_direct_solution: bool
    tool_coverage: float
    quantitative_score: float
    qualitative_label: str

class TraceRunComparison(TypedDict):
    run_count: int
    same_input: bool
    unique_trace_ids: int
    same_tool_sequence: bool
    response_shape_stable: bool


TRACE_ID_PATTERN = re.compile(r"^[a-f0-9]{8}$", re.IGNORECASE)
SOCRATIC_MARKERS = (
    "?",
    "was denkst",
    "überleg",
    "versuch",
    "schritt",
    "hinweis",
    "lass uns",
)
DIRECT_SOLUTION_MARKERS = (
    "die lösung ist",
    "die antwort lautet",
    "hier ist die komplette lösung",
    "musterlösung",
)


@dataclass(frozen=True)
class ChatRun:
    variant: str
    input_text: str
    response_text: str
    trace_id: str
    tool_calls: tuple[str, ...] = ()
    expected_tools: tuple[str, ...] = ()


def evaluate_chat_run(run: ChatRun) -> ChatRunMetrics:
    """Return quantitative and qualitative scores for one chat run."""
    response_lower = run.response_text.lower()
    expected_tools = set(run.expected_tools)
    actual_tools = set(run.tool_calls)

    tool_coverage = (
        len(expected_tools & actual_tools) / len(expected_tools)
        if expected_tools
        else 1.0
    )
    asks_or_guides = any(marker in response_lower for marker in SOCRATIC_MARKERS)
    avoids_direct_solution = not any(
        marker in response_lower for marker in DIRECT_SOLUTION_MARKERS
    )
    has_trace_id = bool(TRACE_ID_PATTERN.fullmatch(run.trace_id))
    has_non_empty_response = bool(run.response_text.strip())

    quantitative_score = mean(
        [
            float(has_non_empty_response),
            float(has_trace_id),
            float(asks_or_guides),
            float(avoids_direct_solution),
            tool_coverage,
        ]
    )

    return {
        "variant": run.variant,
        "has_non_empty_response": has_non_empty_response,
        "has_trace_id": has_trace_id,
        "asks_or_guides": asks_or_guides,
        "avoids_direct_solution": avoids_direct_solution,
        "tool_coverage": round(tool_coverage, 2),
        "quantitative_score": round(quantitative_score, 2),
        "qualitative_label": qualitative_label(quantitative_score, asks_or_guides, avoids_direct_solution),
    }


def qualitative_label(
    quantitative_score: float,
    asks_or_guides: bool,
    avoids_direct_solution: bool,
) -> str:
    if quantitative_score >= 0.9 and asks_or_guides and avoids_direct_solution:
        return "socratic_stable"
    if quantitative_score >= 0.7 and avoids_direct_solution:
        return "usable_with_minor_gaps"
    return "needs_attention"


def compare_trace_runs(runs: list[ChatRun]) -> TraceRunComparison:
    """Compare repeated runs with the same input for trace-level stability."""
    if not runs:
        return {
            "run_count": 0,
            "same_input": False,
            "unique_trace_ids": 0,
            "same_tool_sequence": False,
            "response_shape_stable": False,
        }

    first_input = runs[0].input_text
    first_tool_sequence = runs[0].tool_calls
    first_response_has_question = "?" in runs[0].response_text

    return {
        "run_count": len(runs),
        "same_input": all(run.input_text == first_input for run in runs),
        "unique_trace_ids": len({run.trace_id for run in runs}),
        "same_tool_sequence": all(run.tool_calls == first_tool_sequence for run in runs),
        "response_shape_stable": all(
            ("?" in run.response_text) == first_response_has_question
            for run in runs
        ),
    }
