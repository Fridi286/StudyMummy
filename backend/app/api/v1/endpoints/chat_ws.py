import uuid
import json
from datetime import datetime
from typing import Annotated, cast
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.db.session import AsyncSessionLocal
from app.db.models import User, ChatroomMember, ChatMessage
from app.core.config import get_settings
from app.websockets.manager import manager, WebSocketMessage
from .social import UserPublic

router = APIRouter()
settings = get_settings()

async def get_user_from_token(token: str) -> User | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])  # type: ignore
        user_id = payload.get("sub")
        if not user_id:
            return None
    except Exception:
        return None
        
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()


@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=1008)
        return
        
    await manager.connect(user.user_id, websocket)
    user_data = cast(dict[str, str | int | None], UserPublic.model_validate(user).model_dump())
    
    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue
                
            msg_type = data.get("type")
            if msg_type == "CHAT_MESSAGE":
                room_id = data.get("room_id")
                content = data.get("content")
                
                if not room_id or not content:
                    continue
                    
                async with AsyncSessionLocal() as db:
                    # Verify membership
                    mem_stmt = select(ChatroomMember).where(
                        ChatroomMember.room_id == room_id,
                        ChatroomMember.user_id == user.user_id
                    )
                    is_member = (await db.execute(mem_stmt)).scalars().first()
                    
                    if not is_member:
                        continue
                        
                    # Save message
                    msg_id = str(uuid.uuid4())
                    new_msg = ChatMessage(
                        message_id=msg_id,
                        room_id=room_id,
                        sender_id=user.user_id,
                        content=content
                    )
                    db.add(new_msg)
                    await db.commit()
                    await db.refresh(new_msg)
                    
                    # Broadcast to all members in room
                    room_mem_stmt = select(ChatroomMember).where(ChatroomMember.room_id == room_id)
                    all_members = (await db.execute(room_mem_stmt)).scalars().all()
                    
                    broadcast_msg: WebSocketMessage = {
                        "type": "CHAT_MESSAGE",
                        "message": {
                            "message_id": msg_id,
                            "room_id": room_id,
                            "sender_id": user.user_id,
                            "content": content,
                            "created_at": new_msg.created_at.isoformat(),
                            "sender": user_data
                        }
                    }
                    
                    for m in all_members:
                        await manager.send_personal_message(m.user_id, broadcast_msg)
                        
    except WebSocketDisconnect:
        manager.disconnect(user.user_id, websocket)
