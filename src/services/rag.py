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
from src.services.memvid import memvid


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
            logger.success("RAG service initialized with GLM 4.7 agent")
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

            # Retrieve context if RAG is enabled
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
        use_rag: bool = True,
        k: int = 5,
    ) -> AsyncGenerator[str, None]:
        """Query with RAG and stream response.

        Args:
            query: User's question or request
            use_rag: Whether to use RAG for context (default: True)
            k: Number of documents to retrieve (default: 5)

        Yields:
            Response chunks as they're generated
        """
        try:
            context_docs = []

            # Retrieve context if RAG is enabled
            if use_rag:
                context_docs = self._retrieve_documents(query, k=k)
                logger.info(f"Retrieved {len(context_docs)} documents for RAG")

            # Stream response
            async with self.agent.run_stream(query) as result:
                async for chunk in result:
                    logger.debug(f"Streamed chunk length: {len(chunk.content)}")
                    yield chunk.content

            logger.info(f"Streaming completed for query length: {len(query)}")

        except Exception as e:
            logger.error(f"RAG streaming failed: {e}")
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
            content = doc.get("text", "")[:500]  # Truncate long content

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
