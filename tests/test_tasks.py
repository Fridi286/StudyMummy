"""
Tests für den Task-Endpunkt (deterministisch, kein LLM benötigt).
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_TASK = {
    "task_id": "test_01",
    "subject": "Mathematik",
    "topic": "Lineare Funktionen",
    "difficulty": 2,
    "task_text": "Bestimme die Nullstelle von f(x) = 2x + 4.",
    "required_concepts": ["lineare Funktion", "Nullstelle"],
    "status": "open",
}


def test_create_task():
    r = client.post("/api/v1/tasks/", json=SAMPLE_TASK)
    assert r.status_code == 201
    data = r.json()
    assert data["task_id"] == "test_01"
    assert data["status"] == "open"


def test_get_task():
    r = client.get("/api/v1/tasks/test_01")
    assert r.status_code == 200
    assert r.json()["topic"] == "Lineare Funktionen"


def test_update_task_status():
    r = client.patch("/api/v1/tasks/test_01", json={"status": "solved"})
    assert r.status_code == 200
    assert r.json()["status"] == "solved"


def test_list_tasks():
    r = client.get("/api/v1/tasks/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_delete_task():
    r = client.delete("/api/v1/tasks/test_01")
    assert r.status_code == 204
    r2 = client.get("/api/v1/tasks/test_01")
    assert r2.status_code == 404
