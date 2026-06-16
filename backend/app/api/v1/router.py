from fastapi import APIRouter
from app.api.v1.endpoints import agent, memory, tasks, auth

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(agent.router)
api_router.include_router(memory.router)
api_router.include_router(tasks.router)
