"""
Integrationstests für Agent-Endpunkte (ohne echten LLM-Call).
"""
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.api.dependencies import get_current_user
from app.db.models import User
from app.models.memory import WorkingMemory, LearningProfile

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
    mock_tasks = [{"task_id": "t1", "subject": "Mathe", "topic": "Test", 
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
    """Testet den Chat-Endpunkt mit gemocktem LLM."""
    with patch(
        "app.api.v1.endpoints.agent._llm.chat_with_tools",
        new_callable=AsyncMock,
        return_value=("Was weißt du über lineare Funktionen?", []),
    ), patch(
        "app.api.v1.endpoints.agent.get_or_create_session", new_callable=AsyncMock, return_value=WorkingMemory(session_id="sess_1")
    ), patch(
        "app.api.v1.endpoints.agent.append_dialog", new_callable=AsyncMock
    ), patch(
        "app.api.v1.endpoints.agent.get_dialog_as_messages", new_callable=AsyncMock, return_value=[]
    ):
        r = client.post("/api/v1/agent/chat", json={
            "session_id": "sess_1",
            "user_id": "user_42",
            "message": "Ich verstehe die Nullstelle nicht",
            "task_id": "task_01",
        })
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    # Semantische Assertion: Antwort ist keine leere Zeichenkette
    assert len(data["message"]) > 0
    assert "trace_id" in data
