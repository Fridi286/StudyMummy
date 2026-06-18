import uuid
from typing import Annotated, ClassVar
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc
from pydantic import BaseModel, ConfigDict

from app.db.session import get_async_db
from app.db.models import User, Friendship, Chatroom, ChatroomMember, ChatMessage
from app.api.dependencies import get_current_user
from app.websockets.manager import manager

router = APIRouter()

# --- Schemas ---

class UserPublic(BaseModel):
    user_id: str
    username: str
    first_name: str
    last_name: str
    avatar_url: str | None = None
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

class FriendshipResponse(BaseModel):
    friendship_id: str
    user_id: str
    friend_id: str
    status: str
    created_at: datetime
    friend: UserPublic  # The OTHER user in the friendship
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

class ChatroomResponse(BaseModel):
    room_id: str
    name: str | None = None
    is_group: bool
    created_at: datetime
    members: list[UserPublic]
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

class ChatMessageResponse(BaseModel):
    message_id: str
    room_id: str
    sender_id: str
    content: str
    created_at: datetime
    sender: UserPublic
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

class FriendsResponse(BaseModel):
    friends: list[FriendshipResponse]
    pending_incoming: list[FriendshipResponse]
    pending_outgoing: list[FriendshipResponse]

# --- Endpoints ---

@router.get("/friends/search", response_model=list[UserPublic])
async def search_users(
    query: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> list[User]:
    if len(query) < 1:
        return []
    
    stmt = select(User).where(
        User.username.ilike(f"%{query}%"),
        User.user_id != current_user.user_id
    ).limit(10)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/friends", response_model=FriendsResponse)
async def get_friends(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    # Get all friendships where current user is involved
    stmt = select(Friendship).where(
        or_(
            Friendship.user_id == current_user.user_id,
            Friendship.friend_id == current_user.user_id
        )
    )
    result = await db.execute(stmt)
    friendships = result.scalars().all()

    # To easily populate the 'friend' field for the response
    friends: list[FriendshipResponse] = []
    pending_incoming: list[FriendshipResponse] = []
    pending_outgoing: list[FriendshipResponse] = []

    for f in friendships:
        # Load the other user
        other_user_id = f.friend_id if f.user_id == current_user.user_id else f.user_id
        stmt_user = select(User).where(User.user_id == other_user_id)
        other_user = (await db.execute(stmt_user)).scalars().first()
        
        if not other_user:
            continue
            
        friend_resp = FriendshipResponse(
            friendship_id=f.friendship_id,
            user_id=f.user_id,
            friend_id=f.friend_id,
            status=f.status,
            created_at=f.created_at,
            friend=UserPublic.model_validate(other_user)
        )
        
        if f.status == 'accepted':
            friends.append(friend_resp)
        elif f.status == 'pending':
            if f.friend_id == current_user.user_id:
                pending_incoming.append(friend_resp)
            else:
                pending_outgoing.append(friend_resp)

    return FriendsResponse(
        friends=friends,
        pending_incoming=pending_incoming,
        pending_outgoing=pending_outgoing
    )


@router.post("/friends/request/{target_user_id}")
async def send_friend_request(
    target_user_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    if target_user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")

    # Check if already exists
    stmt = select(Friendship).where(
        or_(
            and_(Friendship.user_id == current_user.user_id, Friendship.friend_id == target_user_id),
            and_(Friendship.user_id == target_user_id, Friendship.friend_id == current_user.user_id)
        )
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Friendship already exists with status: {existing.status}")

    new_friendship = Friendship(
        friendship_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        friend_id=target_user_id,
        status="pending"
    )
    db.add(new_friendship)
    await db.commit()

    # Notify target user via WebSocket
    await manager.send_personal_message(target_user_id, {
        "type": "FRIEND_REQUEST",
        "from_user_id": current_user.user_id,
        "from_username": current_user.username
    })

    return {"message": "Friend request sent"}


@router.post("/friends/accept/{friendship_id}")
async def accept_friend_request(
    friendship_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    stmt = select(Friendship).where(Friendship.friendship_id == friendship_id)
    friendship = (await db.execute(stmt)).scalars().first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")
        
    if friendship.friend_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only accept requests sent to you")
        
    friendship.status = "accepted"
    
    # Check if a direct chatroom exists, if not create one
    room_stmt = select(Chatroom).join(ChatroomMember).where(
        Chatroom.is_group == False,
        Chatroom.room_id.in_(
            select(ChatroomMember.room_id).where(ChatroomMember.user_id == current_user.user_id)
        )
    ).where(
        Chatroom.room_id.in_(
            select(ChatroomMember.room_id).where(ChatroomMember.user_id == friendship.user_id)
        )
    )
    existing_room = (await db.execute(room_stmt)).scalars().first()
    
    if not existing_room:
        room_id = str(uuid.uuid4())
        new_room = Chatroom(room_id=room_id, is_group=False)
        db.add(new_room)
        db.add(ChatroomMember(room_id=room_id, user_id=current_user.user_id))
        db.add(ChatroomMember(room_id=room_id, user_id=friendship.user_id))
    
    await db.commit()

    # Notify original sender
    await manager.send_personal_message(friendship.user_id, {
        "type": "FRIEND_ACCEPTED",
        "from_user_id": current_user.user_id,
        "from_username": current_user.username
    })

    return {"message": "Friend request accepted"}


@router.post("/friends/decline/{friendship_id}")
async def decline_friend_request(
    friendship_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    stmt = select(Friendship).where(Friendship.friendship_id == friendship_id)
    friendship = (await db.execute(stmt)).scalars().first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")
        
    if friendship.friend_id != current_user.user_id and friendship.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await db.delete(friendship)
    await db.commit()
    return {"message": "Friend request declined"}


@router.delete("/friends/{friend_id}")
async def remove_friend(
    friend_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    stmt = select(Friendship).where(
        or_(
            and_(Friendship.user_id == current_user.user_id, Friendship.friend_id == friend_id),
            and_(Friendship.user_id == friend_id, Friendship.friend_id == current_user.user_id)
        )
    )
    friendship = (await db.execute(stmt)).scalars().first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")
        
    await db.delete(friendship)
    
    # Delete direct chatroom
    mem_stmt = select(ChatroomMember.room_id).where(ChatroomMember.user_id == friend_id)
    room_stmt = select(Chatroom).join(ChatroomMember).where(
        Chatroom.is_group == False,
        ChatroomMember.user_id == current_user.user_id,
        Chatroom.room_id.in_(mem_stmt)
    )
    
    room = (await db.execute(room_stmt)).scalars().first()
    if room:
        await db.delete(room)
        
    await db.commit()
    
    # Notify users
    await manager.send_personal_message(friend_id, {
        "type": "FRIEND_REMOVED",
        "from_user_id": current_user.user_id,
        "from_username": current_user.username
    })
    
    return {"message": "Friend removed successfully"}


@router.get("/chatrooms", response_model=list[ChatroomResponse])
async def get_chatrooms(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    stmt = select(Chatroom).join(ChatroomMember).where(ChatroomMember.user_id == current_user.user_id)
    result = await db.execute(stmt)
    chatrooms = result.scalars().all()
    
    response: list[ChatroomResponse] = []
    for room in chatrooms:
        mem_stmt = select(User).join(ChatroomMember).where(ChatroomMember.room_id == room.room_id)
        members = (await db.execute(mem_stmt)).scalars().all()
        
        room_resp = ChatroomResponse(
            room_id=room.room_id,
            name=room.name,
            is_group=room.is_group,
            created_at=room.created_at,
            members=[UserPublic.model_validate(m) for m in members]
        )
        response.append(room_resp)
        
    return response


@router.get("/chatrooms/{room_id}/messages", response_model=list[ChatMessageResponse])
async def get_chat_messages(
    room_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 50,
    offset: int = 0
):
    # Verify membership
    mem_stmt = select(ChatroomMember).where(
        ChatroomMember.room_id == room_id,
        ChatroomMember.user_id == current_user.user_id
    )
    if not (await db.execute(mem_stmt)).scalars().first():
        raise HTTPException(status_code=403, detail="Not a member of this chatroom")
        
    stmt = select(ChatMessage).where(ChatMessage.room_id == room_id).order_by(desc(ChatMessage.created_at)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    messages = list(result.scalars().all())
    
    # We need to reverse because we want chronological order, but we sorted desc to get the latest 50
    messages.reverse()
    
    response: list[ChatMessageResponse] = []
    for msg in messages:
        user_stmt = select(User).where(User.user_id == msg.sender_id)
        sender = (await db.execute(user_stmt)).scalars().first()
        
        msg_resp = ChatMessageResponse(
            message_id=msg.message_id,
            room_id=msg.room_id,
            sender_id=msg.sender_id,
            content=msg.content,
            created_at=msg.created_at,
            sender=UserPublic.model_validate(sender)
        )
        response.append(msg_resp)
        
    return response
