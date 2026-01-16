"""Conversation memory management for Reze AI Agent.

This module handles conversation history storage and retrieval using SQLite.
Each conversation is identified by a unique conversation_id (UUID).
"""

import uuid
from datetime import datetime
from typing import List, Optional

from loguru import logger
from pydantic import BaseModel

from src.database.models import ConversationLog
from src.database.session import async_session_maker


class ChatMessage(BaseModel):
    """Represents a single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ConversationService:
    """Manages conversation history using SQLite."""

    def __init__(self):
        """Initialize conversation service."""
        logger.info("Conversation service initialized")

    async def create_conversation(self) -> str:
        """Create a new conversation with unique ID.

        Returns:
            Unique conversation ID (UUID)
        """
        conversation_id = str(uuid.uuid4())
        logger.info(f"Created new conversation: {conversation_id}")
        return conversation_id

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        """Add a message to conversation history.

        Args:
            conversation_id: Unique conversation identifier
            role: Message role ("user" or "assistant")
            content: Message content
        """
        try:
            async with async_session_maker() as db_session:
                message = ConversationLog(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                )
                db_session.add(message)
                await db_session.commit()

            logger.debug(
                f"Added {role} message to {conversation_id}: {content[:50]}..."
            )
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
    ) -> List[ChatMessage]:
        """Retrieve conversation history for a specific conversation.

        Args:
            conversation_id: Unique conversation identifier
            limit: Maximum number of messages to return (None = all)

        Returns:
            List of chat messages in chronological order
        """
        try:
            from sqlalchemy import select

            async with async_session_maker() as db_session:
                stmt = (
                    select(ConversationLog)
                    .where(ConversationLog.conversation_id == conversation_id)
                    .order_by(ConversationLog.timestamp)
                )

                result = await db_session.execute(stmt)
                db_messages = result.scalars().all()

                # Convert to ChatMessage objects
                messages = [
                    ChatMessage(
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp,
                    )
                    for msg in db_messages
                ]

                # Apply limit if specified
                if limit:
                    messages = messages[-limit:]

                logger.info(f"Retrieved {len(messages)} messages for {conversation_id}")
                return messages

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    async def list_conversations(self) -> List[str]:
        """List all active conversation IDs.

        Returns:
            List of conversation IDs
        """
        try:
            from sqlalchemy import func, select

            async with async_session_maker() as db_session:
                # Get distinct conversation IDs
                stmt = select(ConversationLog.conversation_id).distinct()
                result = await db_session.execute(stmt)
                conversations = result.scalars().all()

                conversation_ids = list(conversations)

                logger.info(f"Found {len(conversation_ids)} active conversations")
                return conversation_ids

        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []

    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation and all its messages.

        Args:
            conversation_id: Unique conversation identifier to delete
        """
        try:
            from sqlalchemy import delete

            async with async_session_maker() as db_session:
                stmt = delete(ConversationLog).where(
                    ConversationLog.conversation_id == conversation_id
                )
                await db_session.execute(stmt)
                await db_session.commit()

            logger.info(f"Deleted conversation: {conversation_id}")

        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            raise

    async def get_conversation_stats(
        self,
        conversation_id: str,
    ) -> dict:
        """Get statistics about a specific conversation.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Dictionary with message count, first/last timestamps, etc.
        """
        try:
            from sqlalchemy import func, select

            async with async_session_maker() as db_session:
                # Count messages
                stmt = select(ConversationLog).where(
                    ConversationLog.conversation_id == conversation_id
                )
                result = await db_session.execute(stmt)
                messages = result.scalars().all()

                if not messages:
                    return {
                        "conversation_id": conversation_id,
                        "message_count": 0,
                        "exists": False,
                    }

                # Get stats
                stats = {
                    "conversation_id": conversation_id,
                    "message_count": len(messages),
                    "first_message": messages[0].timestamp,
                    "last_message": messages[-1].timestamp,
                    "exists": True,
                }

                # Count by role
                user_count = sum(1 for m in messages if m.role == "user")
                assistant_count = sum(1 for m in messages if m.role == "assistant")

                stats["user_messages"] = user_count
                stats["assistant_messages"] = assistant_count

                logger.info(f"Retrieved stats for {conversation_id}")
                return stats

        except Exception as e:
            logger.error(f"Failed to get conversation stats: {e}")
            return {
                "conversation_id": conversation_id,
                "message_count": 0,
                "exists": False,
            }


# Global singleton instance
conversation_service = ConversationService()
