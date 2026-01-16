"""Chat API schemas for Reze AI Agent.

This module defines Pydantic schemas for the chat interface,
which is the only way to interact with Reze (chat-only agent).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chatting with Reze AI Agent.

    This is the primary input for all interactions with the agent.
    The agent will process the message and respond naturally,
    calling tools as needed based on the conversation.
    """

    message: str = Field(
        ...,
        description="User's message to the AI agent",
        min_length=1,
        max_length=10000,
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID for context tracking. Auto-generated if not provided.",
        min_length=1,
        max_length=36,
    )
    streaming: bool = Field(
        default=True,
        description="Always true - native FastAPI streaming for real-time responses",
    )


class ChatMessage(BaseModel):
    """Represents a single message in a conversation."""

    role: str = Field(
        ...,
        description="Message role: 'user' or 'assistant'",
        pattern="^(user|assistant)$",
    )
    content: str = Field(
        ...,
        description="Message content",
        min_length=1,
        max_length=50000,
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="ISO format timestamp when message was created",
    )


class ConversationHistoryResponse(BaseModel):
    """Response schema for retrieving conversation history.

    Returns all messages in a specific conversation session.
    """

    conversation_id: str = Field(
        ...,
        description="Unique conversation identifier",
        min_length=1,
        max_length=36,
    )
    messages: List[ChatMessage] = Field(
        ...,
        description="List of messages in chronological order",
        min_items=0,
    )
    message_count: int = Field(
        ...,
        description="Total number of messages in this conversation",
        ge=0,
    )


class ConversationsListResponse(BaseModel):
    """Response schema for listing all active conversations.

    Returns a list of all conversation IDs for debugging/admin purposes.
    """

    conversations: List[str] = Field(
        ...,
        description="List of conversation IDs",
        min_items=0,
    )
    total: int = Field(
        ...,
        description="Total number of conversations",
        ge=0,
    )


class ConversationCreatedResponse(BaseModel):
    """Response when a new conversation is created."""

    conversation_id: str = Field(
        ...,
        description="Newly generated conversation ID",
        min_length=1,
        max_length=36,
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when conversation was created",
    )


class ConversationDeletedResponse(BaseModel):
    """Response when a conversation is deleted."""

    conversation_id: str = Field(
        ...,
        description="ID of the deleted conversation",
        min_length=1,
        max_length=36,
    )
    deleted: bool = Field(
        ...,
        description="Confirmation that deletion was successful",
    )
