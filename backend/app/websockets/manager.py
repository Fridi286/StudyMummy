from fastapi import WebSocket
from typing_extensions import TypedDict

class ChatMessagePayload(TypedDict, total=False):
    message_id: str
    room_id: str
    sender_id: str
    content: str
    created_at: str
    sender: dict[str, str | int | None]

class WebSocketMessage(TypedDict, total=False):
    type: str
    from_user_id: str
    from_username: str
    user_id: str
    username: str
    message: str | ChatMessagePayload
    session_id: str

from app.core.logging import get_logger

log = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        # Maps user_id to a set of active WebSocket connections
        # A user might be connected from multiple devices/tabs
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        log.info(f"WebSocket connected for user {user_id}. Total connections for user: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            log.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, user_id: str, message: WebSocketMessage):
        """Sends a JSON message to all active connections of a specific user."""
        if user_id in self.active_connections:
            # Create a copy of the set to iterate over, in case a connection drops during iteration
            for connection in list(self.active_connections[user_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    log.warning(f"Failed to send personal message to {user_id}: {e}")
                    self.disconnect(user_id, connection)


manager = ConnectionManager()
