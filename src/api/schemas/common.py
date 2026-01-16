"""Pydantic schemas for common API endpoints.

This module defines response models for health checks, stats,
and conversation management endpoints.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"


class RAGStatsResponse(BaseModel):
    """RAG service statistics response."""

    document_count: Optional[int] = None
    vector_store_status: Optional[str] = None

    class Config:
        extra = "allow"


class ConversationHistoryResponse(BaseModel):
    """Conversation history response."""

    phone_number: str
    message_count: int
    messages: list[dict[str, Any]]


class ConversationClearResponse(BaseModel):
    """Conversation clear response."""

    message: str


class AllConversationsResponse(BaseModel):
    """All conversations response."""

    total_conversations: int
    conversations: dict[str, Any]


class StatsQueryParams(BaseModel):
    """Query parameters for stats endpoint."""

    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class StatsSummaryQueryParams(BaseModel):
    """Query parameters for stats summary endpoint."""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    group_by: str = Field(default="hour", pattern="^(hour|day)$")


class StatsListResponse(BaseModel):
    """Paginated stats list response."""

    total: int
    limit: int
    offset: int
    stats: list[dict[str, Any]]


class StatsSummaryResponse(BaseModel):
    """Aggregated stats summary response."""

    summary: list[dict[str, Any]]
    totals: dict[str, Any]
    group_by: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
