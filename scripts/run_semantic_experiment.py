from statistics import mean

from app.evaluation.metrics import ChatRun, compare_trace_runs, evaluate_chat_run


RUNS = [
    ChatRun(
        variant="baseline_without_tools",
        input_text="Ich verstehe die Nullstelle nicht.",
        response_text="Die Lösung ist x = -2.",
        trace_id="missing",
        tool_calls=(),
        expected_tools=("evaluate_answer",),
    ),
    ChatRun(
        variant="baseline_without_tools",
        input_text="Ich verstehe die Nullstelle nicht.",
        response_text="Du musst x = -2 einsetzen.",
        trace_id="",
        tool_calls=(),
        expected_tools=("evaluate_answer",),
    ),
    ChatRun(
        variant="baseline_without_tools",
        input_text="Ich verstehe die Nullstelle nicht.",
        response_text="Die Antwort lautet -2.",
        trace_id="bad",
        tool_calls=(),
        expected_tools=("evaluate_answer",),
    ),
    ChatRun(
        variant="react_with_tools_and_tracing",
        input_text="Ich verstehe die Nullstelle nicht.",
        response_text="Gute Frage: Was bedeutet es, wenn der Graph die x-Achse schneidet?",
        trace_id="a3f9b1c2",
        tool_calls=("evaluate_answer",),
        expected_tools=("evaluate_answer",),
    ),
    ChatRun(
        variant="react_with_tools_and_tracing",
        input_text="Ich verstehe die Nullstelle nicht.",
        response_text="Welche Stelle am Graphen würdest du zuerst betrachten?",
        trace_id="b4e8c2d1",
        tool_calls=("evaluate_answer",),
        expected_tools=("evaluate_answer",),
    ),
    ChatRun(
        variant="react_with_tools_and_tracing",
        input_text="Ich verstehe die Nullstelle nicht.",
        response_text="Lass uns Schritt für Schritt überlegen: Wo liegt der Schnittpunkt mit der x-Achse?",
        trace_id="c7d1e9a4",
        tool_calls=("evaluate_answer",),
        expected_tools=("evaluate_answer",),
    ),
]


def main() -> None:
    rows = [evaluate_chat_run(run) for run in RUNS]
    variants = sorted({run.variant for run in RUNS})

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

    trace_comparison = compare_trace_runs(
        [run for run in RUNS if run.variant == "react_with_tools_and_tracing"][:2]
    )
    print()
    print("Trace comparison:", trace_comparison)


if __name__ == "__main__":
    main()
