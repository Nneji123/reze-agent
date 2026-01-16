"""RAG (Retrieval-Augmented Generation) service using Memvid.

This module provides intelligent responses by combining:
- Retrieval from Memvid knowledge base (Resend.com docs)
- Generation using GLM 4.7 AI model
- Streaming support for real-time responses
- Multi-turn conversation context
"""

from typing import AsyncGenerator, Dict, List, Optional

from loguru import logger
from pydantic_ai import Agent

from src.services.ai import ai_service
from src.services.memvid import memvid as memvid_service


class RAGService:
    """Service for Retrieval-Augmented Generation."""

    def __init__(self):
        """Initialize RAG service."""
        self.agent = None
        self._initialize()

    def _initialize(self):
        """Initialize AI agent with tools."""
        try:
            self.agent = ai_service.get_agent()

            # Verify agent has tools registered
            logger.info("=== RAG Service Agent Verification ===")
            logger.info(f"Agent type: {type(self.agent).__name__}")
            logger.info(f"Agent name: {self.agent.name}")

            if hasattr(self.agent, "tools"):
                if self.agent.tools:
                    logger.info(f"Agent has {len(self.agent.tools)} tools registered:")
                    for tool_name in self.agent.tools.keys():
                        logger.info(f"  - {tool_name}")
                else:
                    logger.warning("Agent tools attribute exists but is empty!")
            else:
                logger.warning("Agent does not have a tools attribute")

            # Check model configuration
            if hasattr(self.agent, "model"):
                logger.info(f"Agent model: {self.agent.model}")

            logger.success("RAG service initialized with GLM 4.7 agent")
            logger.info("=== End RAG Service Agent Verification ===")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise

    async def query(
        self,
        query: str,
        use_rag: bool = True,
        k: int = 5,
    ) -> Dict:
        """Query with optional RAG (non-streaming).

        Args:
            query: User's question or request
            use_rag: Whether to use RAG for context (default: True)
            k: Number of documents to retrieve (default: 5)

        Returns:
            Dictionary with message, context, and tools_called
        """
        try:
            context_docs = []

            if use_rag:
                context_docs = self._retrieve_documents(query, k=k)
                logger.info(f"Retrieved {len(context_docs)} documents for RAG")

            # Generate response
            result = await self.agent.run(query)

            return {
                "message": result.data,
                "context": context_docs,
                "tools_called": result.tool_calls
                if hasattr(result, "tool_calls")
                else None,
                "use_rag": use_rag,
            }

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise

    async def query_stream(
        self,
        query: str,
        conversation_history: list = None,
        use_rag: bool = True,
        k: int = 5,
    ) -> AsyncGenerator[str, None]:
        """Query with RAG and stream response.

        Args:
            query: User's question or request
            conversation_history: List of previous messages for context
            use_rag: Whether to use RAG for context (default: True)
            k: Number of documents to retrieve (default: 5)

        Yields:
            Response chunks as they're generated
        """
        try:
            context_docs = []

            if use_rag:
                context_docs = self._retrieve_documents(query, k=k)
                logger.info(f"Retrieved {len(context_docs)} documents for RAG")

            # Build the prompt with conversation history
            if conversation_history and len(conversation_history) > 0:
                # Format conversation history as a string for the AI agent
                logger.info(
                    f"Using conversation history with {len(conversation_history)} messages"
                )

                # Log breakdown of messages
                user_msgs = [m for m in conversation_history if m.get("role") == "user"]
                assistant_msgs = [
                    m for m in conversation_history if m.get("role") == "assistant"
                ]
                logger.info(
                    f"History breakdown: {len(user_msgs)} user messages, {len(assistant_msgs)} assistant messages"
                )

                # Log first and last messages for context
                if conversation_history:
                    first_msg = conversation_history[0]
                    last_msg = conversation_history[-1]
                    logger.info(
                        f"History span: First message ({first_msg.get('role')}) at {first_msg.get('timestamp', 'N/A')}, "
                        f"Last message ({last_msg.get('role')}) at {last_msg.get('timestamp', 'N/A')}"
                    )
                    logger.debug(
                        f"First message preview: {first_msg.get('content', '')[:100]}..."
                    )
                    if len(conversation_history) > 1:
                        logger.debug(
                            f"Last message preview: {last_msg.get('content', '')[:100]}..."
                        )

                # Format conversation history as a string that the AI agent can understand
                history_text = "Here is our previous conversation:\n\n"
                for msg in conversation_history:
                    role = msg.get("role", "user").upper()
                    content = msg.get("content", "")
                    history_text += f"{role}: {content}\n\n"

                # Add current query to the history
                prompt = history_text + f"\n\nNow respond to this: {query}"

                logger.info(
                    f"Built prompt with conversation history (total length: {len(prompt)} chars)"
                )
            else:
                # No history, use the query directly
                logger.info("No conversation history, using query directly")
                prompt = query

            logger.info(f"Current query: '{query[:100]}...' (length: {len(query)})")
            logger.debug(f"Prompt type: {type(prompt).__name__}, length: {len(prompt)}")

            async with self.agent.run_stream(prompt) as result:
                previous_text = ""
                total_chunks = 0
                total_delta = 0

                async for chunk in result.stream():
                    total_chunks += 1
                    logger.debug(
                        f"Streamed chunk #{total_chunks}, cumulative length: {len(chunk)}"
                    )

                    if len(chunk) > len(previous_text):
                        delta = chunk[len(previous_text) :]
                        if delta:
                            total_delta += len(delta)
                            logger.debug(f"Yielding delta of length: {len(delta)}")
                            yield delta
                        previous_text = chunk

            logger.info(
                f"Streaming completed: {total_chunks} chunks, "
                f"{total_delta} characters of new content, "
                f"query length: {len(query)}"
            )

        except Exception as e:
            logger.error(
                f"RAG streaming failed for query '{query[:50]}...': {e}", exc_info=True
            )
            raise

    def _retrieve_documents(
        self,
        query: str,
        k: int = 5,
        mode: str = "hybrid",
    ) -> List[Dict]:
        """Retrieve relevant documents from Memvid.

        Args:
            query: Search query
            k: Number of results to return
            mode: Search mode ("lex", "sem", or "hybrid")

        Returns:
            List of document dictionaries
        """
        try:
            results = memvid_service.search(
                query=query,
                k=k,
                mode=mode,
            )
            logger.info(f"Memvid search found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []

    def _build_context(
        self,
        documents: List[Dict],
        max_tokens: int = 2000,
    ) -> str:
        """Build context string from retrieved documents.

        Args:
            documents: List of document dictionaries
            max_tokens: Maximum context tokens

        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant documentation found."

        context_parts = []
        total_length = 0

        for doc in documents:
            title = doc.get("title", "Untitled")
            content = doc.get("text", "")[:500]

            context_part = f"## {title}\n{content}\n"
            context_parts.append(context_part)

            total_length += len(context_part)

            if total_length >= max_tokens:
                break

        context = "\n\n".join(context_parts)
        logger.debug(f"Context built (length: {len(context)})")
        return context

    async def enrich_knowledge_base(self) -> Dict:
        """Enrich Memvid with entity extraction.

        This runs Memvid's entity enrichment to identify
        people, organizations, concepts, etc.

        Returns:
            Statistics about enrichment
        """
        try:
            logger.info("Starting knowledge base enrichment...")
            success = memvid.enrich_entities()

            stats = memvid.get_stats()

            return {
                "success": success,
                "stats": stats,
            }

        except Exception as e:
            logger.error(f"Failed to enrich knowledge base: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_knowledge_stats(self) -> Dict:
        """Get statistics about knowledge base.

        Returns:
            Dictionary with statistics
        """
        try:
            stats = memvid.get_stats()
            doc_count = memvid.count_documents()

            return {
                **stats,
                "document_count": doc_count,
            }

        except Exception as e:
            logger.error(f"Failed to get knowledge stats: {e}")
            return {}


# Global singleton instance
rag_service = RAGService()
