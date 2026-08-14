from app.evaluation.metrics import ChatRun, compare_trace_runs, evaluate_chat_run
from scripts.run_semantic_experiment import study_mummy_react_run

import pytest


def test_evaluate_chat_run_scores_socratic_tool_use_semantically():
    run = ChatRun(
        variant="tool_use",
        input_text="Ich verstehe die Nullstelle nicht.",
        response_text="Gute Frage: Was bedeutet es, wenn der Graph die x-Achse schneidet?",
        trace_id="a3f9b1c2",
        tool_calls=("evaluate_answer",),
        expected_tools=("evaluate_answer",),
    )

    result = evaluate_chat_run(run)

    assert result["has_non_empty_response"] is True
    assert result["has_trace_id"] is True
    assert result["asks_or_guides"] is True
    assert result["avoids_direct_solution"] is True
    assert result["tool_coverage"] == 1.0
    assert result["qualitative_label"] == "socratic_stable"


def test_evaluate_chat_run_flags_direct_solution_risk():
    run = ChatRun(
        variant="baseline",
        input_text="Gib mir die Lösung.",
        response_text="Die Lösung ist x = -2.",
        trace_id="bad",
        tool_calls=(),
        expected_tools=("evaluate_answer",),
    )

    result = evaluate_chat_run(run)

    assert result["has_trace_id"] is False
    assert result["avoids_direct_solution"] is False
    assert result["tool_coverage"] == 0.0
    assert result["qualitative_label"] == "needs_attention"


def test_compare_trace_runs_detects_stable_repeated_input():
    runs = [
        ChatRun(
            variant="tool_use",
            input_text="Was ist eine Nullstelle?",
            response_text="Was weißt du schon über den Schnittpunkt mit der x-Achse?",
            trace_id="11111111",
            tool_calls=("evaluate_answer",),
        ),
        ChatRun(
            variant="tool_use",
            input_text="Was ist eine Nullstelle?",
            response_text="Welche Stelle am Graphen würdest du dafür betrachten?",
            trace_id="22222222",
            tool_calls=("evaluate_answer",),
        ),
    ]

    comparison = compare_trace_runs(runs)

    assert comparison["run_count"] == 2
    assert comparison["same_input"] is True
    assert comparison["unique_trace_ids"] == 2
    assert comparison["same_tool_sequence"] is True
    assert comparison["response_shape_stable"] is True


@pytest.mark.asyncio
async def test_semantic_experiment_uses_openai_compatible_function_tool_call():
    run = await study_mummy_react_run(
        trace_id="a3f9b1c2",
        user_answer="Ich weiss es nicht",
        final_response="Welche Bedeutung hat der Schnittpunkt mit der x-Achse?",
    )

    assert run.response_text.endswith("?")
    assert run.tool_calls == ("evaluate_answer",)
