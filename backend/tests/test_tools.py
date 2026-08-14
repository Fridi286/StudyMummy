"""
Tests für die Agent-Tools ohne Live-API.
Semantische Assertions statt fragiler exakter Stringvergleiche.
"""
import pytest
from app.tools.study_tools import (
    _evaluate_answer,
    _update_learning_profile,
    _generate_quiz_questions,
    _create_cheatsheet,
    _award_coins_and_exp,
    _add_calendar_note,
)
from app.core.context import current_user_id
from app.tools.registry import get


@pytest.mark.asyncio
async def test_evaluate_answer_correct():
    result = await _evaluate_answer("t1", "Die Nullstelle ist -2", "Nullstelle")
    assert result["is_correct"] is True
    assert result["score"] == 1.0
    assert "task_id" in result


@pytest.mark.asyncio
async def test_evaluate_answer_wrong():
    result = await _evaluate_answer("t1", "Ich weiß es nicht", "Nullstelle")
    assert result["is_correct"] is False
    assert result["score"] == 0.0


@pytest.mark.asyncio
async def test_generate_quiz_questions():
    result = await _generate_quiz_questions("Lineare Funktionen", num_questions=3)
    assert result["topic"] == "Lineare Funktionen"
    assert len(result["questions"]) == 3
    # Semantische Assertion: jede Frage hat Antwortoptionen
    for q in result["questions"]:
        assert len(q["options"]) >= 2
        assert "correct" in q


@pytest.mark.asyncio
async def test_update_learning_profile_clamps_score():
    token = current_user_id.set("user_42")
    try:
        result = await _update_learning_profile("Algebra", 1.5)
        result2 = await _update_learning_profile("Algebra", -0.5)
    finally:
        current_user_id.reset(token)

    assert result["user_id"] == "user_42"
    assert result["new_confidence"] <= 1.0
    assert result2["user_id"] == "user_42"
    assert result2["new_confidence"] >= 0.0


@pytest.mark.asyncio
async def test_update_learning_profile_requires_authenticated_request_context():
    token = current_user_id.set("")
    try:
        result = await _update_learning_profile("Algebra", 0.5)
    finally:
        current_user_id.reset(token)

    assert "error" in result
    assert "authentifizierten Request-Kontext" in result["error"]


def test_update_learning_profile_schema_does_not_accept_model_user_id():
    parameters = get("update_learning_profile").parameters

    assert "user_id" not in parameters["properties"]
    assert parameters["required"] == ["tag", "score"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("start_time", "end_time"),
    [
        ("2026-08-13T12:00:00Z", "2026-08-13T12:00:00Z"),
        ("2026-08-13T12:00:00Z", "2026-08-13T11:59:59Z"),
    ],
)
async def test_add_calendar_note_rejects_non_positive_interval(start_time: str, end_time: str):
    token = current_user_id.set("user_42")
    try:
        result = await _add_calendar_note("Lernen", "Nullstellen", start_time, end_time)
    finally:
        current_user_id.reset(token)

    assert result == {"error": "end_time muss nach start_time liegen"}


@pytest.mark.asyncio
async def test_award_requires_authenticated_request_context():
    token = current_user_id.set("")
    try:
        result = await _award_coins_and_exp(10, "Aufgabe gelöst")
    finally:
        current_user_id.reset(token)
    assert "error" in result
    assert "user_id" in result["error"]
