"""API routers for Reze AI Agent.

This module exports all FastAPI routers. For Reze, there's
only one router: the chat router, which handles all interactions
with the AI agent through a chat-only interface.
"""

from .chat_router import router as chat_router

__all__ = ["chat_router"]
