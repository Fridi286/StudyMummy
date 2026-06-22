from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from app.db.session import Base


class User(Base):
    __tablename__: str = "users"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    coins: Mapped[int] = mapped_column(Integer, default=0)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    learning_profile: Mapped["LearningProfile"] = relationship("LearningProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    confidence_scores: Mapped[list["ConfidenceScore"]] = relationship("ConfidenceScore", back_populates="user", cascade="all, delete-orphan")
    inventory_items: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="user", cascade="all, delete-orphan")
    active_items: Mapped[list["ActiveItem"]] = relationship("ActiveItem", back_populates="user", cascade="all, delete-orphan")

    @property
    def level(self) -> int:
        # A simple leveling formula, e.g., 1 level per 100 xp. 
        # You can adjust this to whatever curve you'd like!
        return (self.experience // 100) + 1


class LearningProfile(Base):
    __tablename__: str = "learning_profiles"

    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    sessions_count: Mapped[int] = mapped_column(Integer, default=0)
    error_patterns: Mapped[list[str]] = mapped_column(JSONB, server_default='[]')
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="learning_profile")





class ConfidenceScore(Base):
    __tablename__: str = "confidence_scores"
    __table_args__: tuple[UniqueConstraint, ...] = (UniqueConstraint("user_id", "tag"),)

    score_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="confidence_scores")


class Document(Base):
    __tablename__: str = "documents"

    document_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, server_default='[]')
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="document", cascade="all, delete-orphan")
    quizzes: Mapped[list["Quiz"]] = relationship("Quiz", back_populates="document", cascade="all, delete-orphan")
    cheatsheets: Mapped[list["Cheatsheet"]] = relationship("Cheatsheet", back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__: str = "document_chunks"

    chunk_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(255), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Any] = mapped_column(Vector(1536))
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    user: Mapped["User"] = relationship("User")



class Task(Base):
    __tablename__: str = "tasks"

    task_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(255), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    key_concepts: Mapped[list[str]] = mapped_column(JSONB, server_default='[]')
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="tasks")


class Quiz(Base):
    __tablename__: str = "quizzes"

    quiz_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(255), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document: Mapped["Document"] = relationship("Document", back_populates="quizzes")
    questions: Mapped[list["QuizQuestion"]] = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts: Mapped[list["QuizAttempt"]] = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizAttempt(Base):
    __tablename__: str = "quiz_attempts"

    attempt_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    quiz_id: Mapped[str] = mapped_column(String(255), ForeignKey("quizzes.quiz_id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    answers: Mapped[dict[str, str]] = mapped_column(JSONB, server_default='{}')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="attempts")


class QuizQuestion(Base):
    __tablename__: str = "quiz_questions"

    question_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    quiz_id: Mapped[str] = mapped_column(String(255), ForeignKey("quizzes.quiz_id", ondelete="CASCADE"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str]] = mapped_column(JSONB, server_default='[]', nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_concepts: Mapped[list[str]] = mapped_column(JSONB, server_default='[]')

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")


class Cheatsheet(Base):
    __tablename__: str = "cheatsheets"

    cheatsheet_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(255), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    key_concepts: Mapped[list[str]] = mapped_column(JSONB, server_default='[]', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document: Mapped["Document"] = relationship("Document", back_populates="cheatsheets")


class Session(Base):
    __tablename__: str = "sessions"

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    current_task_id: Mapped[str | None] = mapped_column(String(255), ForeignKey("tasks.task_id", ondelete="SET NULL"), nullable=True)
    help_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship("User", back_populates="sessions")
    chat_logs: Mapped[list["ChatLog"]] = relationship("ChatLog", back_populates="session", cascade="all, delete-orphan", order_by="ChatLog.timestamp")


class ChatLog(Base):
    __tablename__: str = "chat_logs"

    message_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    action_taken: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session: Mapped["Session"] = relationship("Session", back_populates="chat_logs")


class Friendship(Base):
    __tablename__: str = "friendships"
    __table_args__: tuple[UniqueConstraint, ...] = (UniqueConstraint("user_id", "friend_id"),)

    friendship_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    friend_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    friend: Mapped["User"] = relationship("User", foreign_keys=[friend_id])


class Chatroom(Base):
    __tablename__: str = "chatrooms"

    room_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    members: Mapped[list["ChatroomMember"]] = relationship("ChatroomMember", back_populates="chatroom", cascade="all, delete-orphan")
    messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="chatroom", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatroomMember(Base):
    __tablename__: str = "chatroom_members"

    room_id: Mapped[str] = mapped_column(String(255), ForeignKey("chatrooms.room_id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    chatroom: Mapped["Chatroom"] = relationship("Chatroom", back_populates="members")
    user: Mapped["User"] = relationship("User")


class ChatMessage(Base):
    __tablename__: str = "chat_messages"

    message_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    room_id: Mapped[str] = mapped_column(String(255), ForeignKey("chatrooms.room_id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    chatroom: Mapped["Chatroom"] = relationship("Chatroom", back_populates="messages")
    sender: Mapped["User"] = relationship("User")


class Item(Base):
    __tablename__: str = "items"

    item_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effects: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_buyable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    inventory_items: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="item", cascade="all, delete-orphan")


class InventoryItem(Base):
    __tablename__: str = "inventory_items"
    __table_args__: tuple[UniqueConstraint, ...] = (UniqueConstraint("user_id", "item_id"),)

    inventory_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[str] = mapped_column(String(255), ForeignKey("items.item_id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="inventory_items")
    item: Mapped["Item"] = relationship("Item", back_populates="inventory_items")


class ActiveItem(Base):
    __tablename__: str = "active_items"

    active_item_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[str] = mapped_column(String(255), ForeignKey("items.item_id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    effects: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="active_items")
    item: Mapped["Item"] = relationship("Item")


class SlotMachineLog(Base):
    __tablename__: str = "slot_machine_logs"

    log_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    bet_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payout: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User")


class Trade(Base):
    __tablename__: str = "trades"

    trade_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    sender_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    receiver_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    sender_coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    receiver_coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship("User", foreign_keys=[receiver_id])
    trade_items: Mapped[list["TradeItem"]] = relationship("TradeItem", back_populates="trade", cascade="all, delete-orphan")


class TradeItem(Base):
    __tablename__: str = "trade_items"

    trade_item_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    trade_id: Mapped[str] = mapped_column(String(255), ForeignKey("trades.trade_id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[str] = mapped_column(String(255), ForeignKey("items.item_id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    trade: Mapped["Trade"] = relationship("Trade", back_populates="trade_items")
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    item: Mapped["Item"] = relationship("Item")


