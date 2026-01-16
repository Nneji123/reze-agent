"""Database models for Reze AI Agent.

This module defines SQLAlchemy models for storing chat conversations
and related data. All models use async SQLAlchemy.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from src.database.base import Base


class ConversationLog(Base):
    """Model for storing chat conversation messages.

    This table stores individual messages for each conversation session.
    Conversations are tracked using a unique conversation_id (UUID).

    Attributes:
        id: Primary key
        conversation_id: Unique identifier for the chat session
        role: Message role ("user" or "assistant")
        content: The message content
        timestamp: When the message was created
        tools_used: Optional JSON string of tools called by AI
        rag_context_used: Optional JSON string of RAG context used
    """

    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True, nullable=False)

    username = Column(
        String(50),  # Username identifier
        index=True,
        nullable=False,
        comment="Username identifier for conversation",
    )

    conversation_id = Column(
        String(36),  # UUID format
        index=True,
        nullable=False,
        comment="Unique conversation identifier (UUID)",
    )

    role = Column(
        String(20),  # "user" or "assistant"
        index=True,
        nullable=False,
        comment="Message role",
    )

    content = Column(Text, nullable=False, comment="Message content")

    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
        comment="Message timestamp",
    )

    tools_used = Column(
        Text, nullable=True, comment="JSON string of tools called by AI"
    )

    rag_context_used = Column(
        Text, nullable=True, comment="JSON string of RAG context retrieved"
    )

    def __repr__(self) -> str:
        """String representation of the model."""
        return (
            f"<ConversationLog(id={self.id}, "
            f"username={self.username}, "
            f"conversation_id={self.conversation_id}, "
            f"role={self.role}, "
            f"timestamp={self.timestamp})>"
        )
