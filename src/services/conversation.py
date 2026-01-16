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

    async def create_conversation(self, username: str = "anonymous") -> str:
        """Create a new conversation with unique ID.

        Args:
            username: Username identifier for the conversation

        Returns:
            Unique conversation ID (UUID)
        """
        conversation_id = str(uuid.uuid4())
        logger.info(f"Created new conversation: {conversation_id} for user: {username}")
        return conversation_id

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        username: str = "anonymous",
    ) -> None:
        """Add a message to conversation history.

        Args:
            conversation_id: Unique conversation identifier
            role: Message role ("user" or "assistant")
            content: Message content
            username: Username identifier for the message
        """
        try:
            async with async_session_maker() as db_session:
                message = ConversationLog(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    username=username,
                )
                db_session.add(message)
                await db_session.commit()
                await db_session.refresh(message)

            logger.info(
                f"Added {role} message to {conversation_id} ({username}): {content[:50]}... (ID: {message.id})"
            )
        except Exception as e:
            logger.error(
                f"Failed to add message to {conversation_id}: {e}", exc_info=True
            )
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

                logger.info(
                    f"Database query returned {len(db_messages)} total messages for {conversation_id}"
                )

                # Convert to ChatMessage objects
                messages = [
                    ChatMessage(
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp,
                    )
                    for msg in db_messages
                ]

                # Apply limit if specified (take most recent messages)
                if limit and len(messages) > limit:
                    messages = messages[-limit:]

                # Log message breakdown for debugging
                user_msgs = [m for m in messages if m.role == "user"]
                assistant_msgs = [m for m in messages if m.role == "assistant"]
                logger.info(
                    f"Returning {len(messages)} messages for {conversation_id} "
                    f"({len(user_msgs)} user, {len(assistant_msgs)} assistant, limit: {limit})"
                )

                if messages:
                    logger.debug(
                        f"Oldest message: {messages[0].role} at {messages[0].timestamp}, "
                        f"Newest message: {messages[-1].role} at {messages[-1].timestamp}"
                    )

                return messages
        except Exception as e:
            logger.error(
                f"Failed to get conversation history for {conversation_id}: {e}",
                exc_info=True,
            )
            return []

    async def get_user_conversations(
        self,
        username: str,
    ) -> List[dict]:
        """Get all conversations for a specific user.

        Args:
            username: Username identifier

        Returns:
            List of conversation metadata with ID, message count, etc.
        """
        try:
            from sqlalchemy import func, select

            async with async_session_maker() as db_session:
                # Get distinct conversation IDs for this user
                stmt = (
                    select(
                        ConversationLog.conversation_id,
                        func.min(ConversationLog.timestamp).label("created_at"),
                        func.count(ConversationLog.id).label("message_count"),
                        func.max(ConversationLog.timestamp).label("last_updated"),
                    )
                    .where(ConversationLog.username == username)
                    .group_by(ConversationLog.conversation_id)
                    .order_by(func.max(ConversationLog.timestamp).desc())
                )

                result = await db_session.execute(stmt)
                conversations = result.all()

                conversation_list = [
                    {
                        "conversation_id": conv.conversation_id,
                        "created_at": conv.created_at,
                        "message_count": conv.message_count,
                        "last_updated": conv.last_updated,
                    }
                    for conv in conversations
                ]

                logger.info(
                    f"Retrieved {len(conversation_list)} conversations for user {username}"
                )
                return conversation_list
        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
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
