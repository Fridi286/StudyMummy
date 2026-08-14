"""
Integrationstests für Agent-Endpunkte (ohne echten LLM-Call).
"""
from starlette.testclient import TestClient
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from fastapi import HTTPException
from app.main import app
from app.api.dependencies import get_current_user
from app.db.models import User
from app.models.memory import WorkingMemory, LearningProfile
from app.agents.protocol import (
    AgentAction,
    AgentId,
    AgentIntent,
    AgentLocalState,
    AgentPlan,
    AgentRunResult,
    AgentStep,
)
from app.api.v1.endpoints.agent import _resolve_study_context

async def override_get_current_user():
    return User(user_id="user_42", username="test", email="test@test.com")

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_get_session():
    with patch("app.api.v1.endpoints.memory.get_or_create_session", new_callable=AsyncMock, return_value=WorkingMemory(session_id="test_session")):
        r = client.get("/api/v1/memory/session/test_session")
        assert r.status_code == 200
        data = r.json()
        assert data["session_id"] == "test_session"
        assert "dialog_history" in data


def test_get_learning_profile():
    with patch("app.api.v1.endpoints.memory.get_or_create_profile", new_callable=AsyncMock, return_value=LearningProfile(user_id="user_42")):
        r = client.get("/api/v1/memory/profile")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == "user_42"
        assert "confidence_scores" in data


def test_document_upload_text_file():
    """Testet den Upload-Endpunkt mit einer einfachen Textdatei (kein echter LLM-Call)."""
    mock_tasks = [{"task_id": "t1", "tags": ["Mathe", "Test"], 
                   "difficulty": 1, "task_text": "...", "required_concepts": [], "status": "open"}]
    
    with patch(
        "app.api.v1.endpoints.agent._llm.extract_tasks_from_text",
        new_callable=AsyncMock,
        return_value=mock_tasks,
    ):
        r = client.post(
            "/api/v1/agent/upload",
            files={"file": ("test.txt", b"Aufgabe 1: Berechne 2+2", "text/plain")},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["document_id"] == "test.txt"
    assert len(data["extracted_tasks"]) == 1


def test_document_upload_empty_file_rejected():
    r = client.post(
        "/api/v1/agent/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert r.status_code == 400
    assert "Leere Datei" in r.json()["detail"]


def test_chat_endpoint_mocked():
    """Test the API boundary with a mocked multi-agent run."""
    agent_result = AgentRunResult(
        response="Was weißt du über lineare Funktionen?",
        plan=AgentPlan(
            intent=AgentIntent.REQUEST_HINT,
            action=AgentAction.GIVE_HINT,
            objective="Einen passenden Hinweis geben.",
            decision_basis="Der Nutzer benötigt Hilfe.",
            success_criteria=["Aktivierende Rückfrage"],
        ),
        steps=[AgentStep(agent="planner", phase="plan", summary="Hinweis geplant")],
        agent_states=[AgentLocalState(
            agent=AgentId.PLANNER,
            objective="Einen nächsten Schritt planen.",
            capabilities=["action_selection"],
            decisions_made=1,
        )],
        reviewed=True,
    )
    with patch(
        "app.api.v1.endpoints.agent._orchestrator.run",
        new_callable=AsyncMock,
        return_value=agent_result,
    ) as run_mock, patch(
        "app.api.v1.endpoints.agent._resolve_study_context",
        new_callable=AsyncMock,
        return_value=("doc_1", "Aufgabe: Bestimme die Nullstelle."),
    ), patch(
        "app.api.v1.endpoints.agent.get_or_create_session", new_callable=AsyncMock, return_value=WorkingMemory(session_id="sess_1")
    ), patch(
        "app.api.v1.endpoints.agent.append_dialog", new_callable=AsyncMock
    ), patch(
        "app.api.v1.endpoints.agent.get_dialog_as_messages", new_callable=AsyncMock, return_value=[]
    ), patch(
        "app.api.v1.endpoints.agent.update_session_context",
        new_callable=AsyncMock,
        return_value=WorkingMemory(session_id="sess_1", current_task_id="task_01"),
    ):
        r = client.post("/api/v1/agent/chat", json={
            "session_id": "sess_1",
            "user_id": "user_42",
            "message": "Ich verstehe die Nullstelle nicht",
            "task_id": "task_01",
            "document_id": "doc_1",
        })
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    # Semantische Assertion: Antwort ist keine leere Zeichenkette
    assert len(data["message"]) > 0
    assert "trace_id" in data
    assert data["decision"]["action"] == "give_hint"
    assert data["agents_involved"] == ["planner"]
    assert data["coordination_rounds"] == 1
    assert data["agent_states"][0]["decisions_made"] == 1
    assert data["reviewed"] is True
    agent_context = run_mock.await_args.args[0]
    assert agent_context.document_id == "doc_1"
    assert agent_context.task_context == "Aufgabe: Bestimme die Nullstelle."


@pytest.mark.asyncio
async def test_resolve_study_context_loads_owned_task():
    task = SimpleNamespace(
        task_id="task_01",
        document_id="doc_1",
        task_text="Bestimme die Nullstelle der Funktion.",
        difficulty=2,
        key_concepts=["Lineare Funktion", "Nullstelle"],
        status="open",
    )
    result = MagicMock()
    result.scalars.return_value.first.return_value = task
    db = AsyncMock()
    db.execute.return_value = result

    document_id, task_context = await _resolve_study_context(
        db, "user_42", "task_01", "doc_1"
    )

    assert document_id == "doc_1"
    assert task_context is not None
    assert "Bestimme die Nullstelle" in task_context
    assert "Lineare Funktion, Nullstelle" in task_context


@pytest.mark.asyncio
async def test_resolve_study_context_rejects_unknown_task():
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    db = AsyncMock()
    db.execute.return_value = result

    with pytest.raises(HTTPException) as exc_info:
        await _resolve_study_context(db, "user_42", "foreign_task", None)

    assert getattr(exc_info.value, "status_code", None) == 404
