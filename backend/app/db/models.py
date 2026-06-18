from datetime import datetime, timezone

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    learning_profile: Mapped["LearningProfile"] = relationship("LearningProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    confidence_scores: Mapped[list["ConfidenceScore"]] = relationship("ConfidenceScore", back_populates="user", cascade="all, delete-orphan")


class LearningProfile(Base):
    __tablename__: str = "learning_profiles"

    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    sessions_count: Mapped[int] = mapped_column(Integer, default=0)
    error_patterns: Mapped[list[str]] = mapped_column(JSONB, server_default='[]')
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="learning_profile")


class Subject(Base):
    __tablename__: str = "subjects"

    subject_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    topics: Mapped[list["Topic"]] = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__: str = "topics"
    __table_args__: tuple[UniqueConstraint, ...] = (UniqueConstraint("name", "subject_id"),)

    topic_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(255), ForeignKey("subjects.subject_id", ondelete="CASCADE"), nullable=False)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="topics")


class ConfidenceScore(Base):
    __tablename__: str = "confidence_scores"
    __table_args__: tuple[UniqueConstraint, ...] = (UniqueConstraint("user_id", "subject_id", "topic_id"),)

    score_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(255), ForeignKey("subjects.subject_id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(255), ForeignKey("topics.topic_id", ondelete="CASCADE"), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="confidence_scores")


class Document(Base):
    __tablename__: str = "documents"

    document_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="document", cascade="all, delete-orphan")


class Task(Base):
    __tablename__: str = "tasks"

    task_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(255), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(255), ForeignKey("subjects.subject_id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(255), ForeignKey("topics.topic_id", ondelete="CASCADE"), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    required_concepts: Mapped[list[str]] = mapped_column(JSONB, server_default='[]')
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="tasks")


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
