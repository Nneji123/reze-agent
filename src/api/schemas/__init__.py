"""API schemas (Pydantic models) for request/response validation."""

from .chat import (
    ChatMessage,
    ChatRequest,
    ConversationCreatedResponse,
    ConversationDeletedResponse,
    ConversationHistoryResponse,
    ConversationsListResponse,
)
from .common import ErrorResponse, HealthResponse

__all__ = [
    # Chat schemas
    "ChatRequest",
    "ChatMessage",
    "ConversationCreatedResponse",
    "ConversationDeletedResponse",
    "ConversationHistoryResponse",
    "ConversationsListResponse",
    # Common schemas
    "ErrorResponse",
    "HealthResponse",
]
