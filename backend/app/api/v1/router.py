from fastapi import APIRouter
from app.api.v1.endpoints import auth, agent, tasks, memory, social, chat_ws

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agent.router, tags=["agent"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(social.router, prefix="/social", tags=["social"])
api_router.include_router(chat_ws.router, tags=["chat_ws"])
