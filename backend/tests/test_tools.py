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
)
from app.core.context import current_user_id


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
    result = await _update_learning_profile("user_42", "Algebra", 1.5)
    assert result["new_confidence"] <= 1.0
    result2 = await _update_learning_profile("user_42", "Algebra", -0.5)
    assert result2["new_confidence"] >= 0.0


@pytest.mark.asyncio
async def test_award_requires_authenticated_request_context():
    token = current_user_id.set("")
    try:
        result = await _award_coins_and_exp(10, "Aufgabe gelöst")
    finally:
        current_user_id.reset(token)
    assert "error" in result
    assert "user_id" in result["error"]
