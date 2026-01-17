"""Chat API schemas for Reze AI Agent.

This module defines Pydantic schemas for chat interface,
which is the only way to interact with Reze (chat-only agent).
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chatting with Reze AI Agent.

    This is the primary input for all interactions with the agent.
    The agent will process the message and respond naturally,
    calling tools as needed based on the conversation.
    """

    username: str = Field(
        ...,
        description="Username identifier for the user",
        min_length=1,
        max_length=50,
    )
    message: str = Field(
        ...,
        description="User's message to AI agent",
        min_length=1,
        max_length=10000,
    )
    conversation_id: str | None = Field(
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
    timestamp: datetime | None = Field(
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
    messages: list[ChatMessage] = Field(
        ...,
        description="List of messages in chronological order",
        min_length=0,
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

    conversations: list[str] = Field(
        ...,
        description="List of conversation IDs",
        min_length=0,
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
        description="ID of deleted conversation",
        min_length=1,
        max_length=36,
    )
    deleted: bool = Field(
        ...,
        description="Confirmation that deletion was successful",
    )


class UserConversation(BaseModel):
    """Represents a conversation with metadata."""

    conversation_id: str = Field(
        ...,
        description="Unique conversation identifier",
        min_length=1,
        max_length=36,
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when conversation was created",
    )
    message_count: int = Field(
        ...,
        description="Total number of messages in conversation",
        ge=0,
    )
    last_updated: datetime | None = Field(
        None,
        description="Timestamp of last message in conversation",
    )


class UserConversationsResponse(BaseModel):
    """Response schema for listing user conversations.

    Returns a list of conversations for a specific user
    with metadata like message count and timestamps.
    """

    conversations: list[UserConversation] = Field(
        ...,
        description="List of user's conversations with metadata",
        min_length=0,
    )
    total: int = Field(
        ...,
        description="Total number of conversations for this user",
        ge=0,
    )
