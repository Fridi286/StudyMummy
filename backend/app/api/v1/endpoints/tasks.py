"""
Aufgaben-Endpunkte: CRUD für strukturierte Tasks.
"""
from fastapi import APIRouter, HTTPException
from app.models.task import Task, TaskUpdate

router = APIRouter()

_tasks: dict[str, Task] = {}  # In-Memory; für Produktion: DB-Repository


@router.get("/", response_model=list[Task], summary="Alle Aufgaben")
async def list_tasks():
    return list(_tasks.values())


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    return _tasks[task_id]


@router.post("/", response_model=Task, status_code=201)
async def create_task(task: Task):
    if task.task_id in _tasks:
        raise HTTPException(status_code=409, detail="task_id bereits vergeben")
    _tasks[task.task_id] = task
    return task


@router.patch("/{task_id}", response_model=Task)
async def update_task(task_id: str, update: TaskUpdate):
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    task = _tasks[task_id]
    if update.status is not None:
        task.status = update.status
    if update.difficulty is not None:
        task.difficulty = update.difficulty
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str):
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    del _tasks[task_id]
