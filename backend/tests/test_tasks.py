"""
Tests for persistent task endpoint behavior.
"""
import pytest

from app.api.v1.endpoints import tasks as task_endpoints
from app.db.models import Document, Task, User
from app.models.task import TaskCreate, TaskUpdate


class _FakeScalars:
    def __init__(self, values):
        self._values = values

    def first(self):
        return self._values[0] if self._values else None

    def all(self):
        return self._values


class _FakeResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return _FakeScalars(self._values)


class _FakeDb:
    def __init__(self, *execute_results):
        self.execute_results = list(execute_results)
        self.added = []
        self.deleted = []
        self.committed = False

    async def execute(self, _stmt):
        return _FakeResult(self.execute_results.pop(0))

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)

    async def commit(self):
        self.committed = True

    async def refresh(self, _obj):
        return None


@pytest.fixture
def current_user():
    return User(user_id="user_1", username="jannis", first_name="Jannis", last_name="Test", email="j@example.com", password_hash="x")


@pytest.fixture
def document():
    return Document(document_id="doc_1", user_id="user_1", file_name="blatt.pdf", storage_path="/tmp/blatt.pdf")


@pytest.fixture
def sample_task():
    return Task(
        task_id="task_1",
        document_id="doc_1",
        difficulty=2,
        task_text="Bestimme die Nullstelle von f(x) = 2x + 4.",
        key_concepts=["lineare Funktion", "Nullstelle"],
        status="open",
    )


@pytest.mark.asyncio
async def test_list_tasks_returns_user_tasks(current_user, sample_task):
    db = _FakeDb([sample_task])

    result = await task_endpoints.list_tasks(db=db, current_user=current_user)

    assert result == [sample_task]


@pytest.mark.asyncio
async def test_create_task_persists_task_for_owned_document(current_user, document):
    db = _FakeDb([document])
    task_create = TaskCreate(
        document_id="doc_1",
        difficulty=2,
        task_text="Bestimme die Nullstelle.",
        key_concepts=["Nullstelle"],
    )

    result = await task_endpoints.create_task(task_create, db=db, current_user=current_user)

    assert result in db.added
    assert result.document_id == "doc_1"
    assert result.status == "open"
    assert db.committed is True


@pytest.mark.asyncio
async def test_update_task_status_uses_canonical_status(current_user, sample_task):
    db = _FakeDb([sample_task])

    result = await task_endpoints.update_task("task_1", TaskUpdate(status="solved"), db=db, current_user=current_user)

    assert result.status == "solved"
    assert db.committed is True


@pytest.mark.asyncio
async def test_delete_task_removes_owned_task(current_user, sample_task):
    db = _FakeDb([sample_task])

    await task_endpoints.delete_task("task_1", db=db, current_user=current_user)

    assert db.deleted == [sample_task]
    assert db.committed is True
