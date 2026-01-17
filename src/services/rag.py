"""RAG (Retrieval-Augmented Generation) service using Memvid."""

from typing import AsyncGenerator, Dict, List

from pydantic_ai import Agent

from src.services.ai import ai_service
from src.services.memvid import memvid as memvid_service


class RAGService:
    """Service for Retrieval-Augmented Generation."""

    def __init__(self):
        self.agent = ai_service.get_agent()

    async def query(
        self,
        query: str,
        use_rag: bool = True,
        k: int = 5,
    ) -> Dict:
        """Query with optional RAG (non-streaming)."""
        context_docs = []

        if use_rag:
            context_docs = self._retrieve_documents(query, k=k)

        result = await self.agent.run(query)

        return {
            "message": result.data,
            "context": context_docs,
            "tools_called": result.tool_calls
            if hasattr(result, "tool_calls")
            else None,
            "use_rag": use_rag,
        }

    async def query_stream(
        self,
        query: str,
        conversation_history: list = None,
        use_rag: bool = True,
        k: int = 5,
    ) -> AsyncGenerator[str, None]:
        """Query with RAG and stream response."""
        if use_rag:
            self._retrieve_documents(query, k=k)

        if conversation_history:
            history_text = "\n\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
                for m in conversation_history
            )
            prompt = f"{history_text}\n\nNow respond to this: {query}"
        else:
            prompt = query

        async with self.agent.run_stream(prompt) as result:
            previous_text = ""
            async for chunk in result.stream():
                if len(chunk) > len(previous_text):
                    delta = chunk[len(previous_text) :]
                    if delta:
                        yield delta
                    previous_text = chunk

    def _retrieve_documents(
        self,
        query: str,
        k: int = 5,
        mode: str = "hybrid",
    ) -> List[Dict]:
        """Retrieve relevant documents from Memvid."""
        return memvid_service.search(query=query, k=k, mode=mode)


# Global singleton instance
rag_service = RAGService()
