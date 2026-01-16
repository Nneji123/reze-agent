"""Memvid service for RAG (Retrieval-Augmented Generation).

This module provides an interface to Memvid, a single-file AI memory system
that supports hybrid search (BM25 + semantic vectors), entity extraction,
and O(1) entity lookups.
"""

import os
from typing import Dict, List, Optional

from loguru import logger
from memvid_sdk import create, use

from src.config import settings


class MemvidService:
    """Service for managing Memvid knowledge base."""

    def __init__(self):
        """Initialize Memvid service."""
        self.memvid_path = settings.memvid_file_path
        self.mem = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize Memvid store - create new or load existing."""
        try:
            logger.info(f"Initializing Memvid service at: {self.memvid_path}")

            if os.path.exists(self.memvid_path):
                logger.info("Found existing Memvid store - loading...")
                self.mem = use(
                    kind=settings.memvid_index_kind,
                    filename=self.memvid_path,
                    enable_lex=True,
                    enable_vec=False,
                    mode="open",
                )
                logger.success("Memvid store loaded successfully")
            else:
                logger.info("No existing store found - creating new Memvid store...")
                self.mem = create(
                    filename=self.memvid_path,
                    kind=settings.memvid_index_kind,
                    enable_lex=True,
                    enable_vec=False,
                )
                logger.success("Memvid store created successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Memvid: {e}")
            raise

    async def add_document(
        self,
        text: str,
        title: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Add a document to Memvid knowledge base.

        Args:
            text: Document content to store
            title: Document title
            metadata: Optional metadata dictionary (e.g., url, source, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.mem.put(
                title=title,
                text=text,
                metadata=metadata or {},
            )
            logger.info(f"Document added: '{title}'")
            return True
        except Exception as e:
            logger.error(f"Failed to add document '{title}': {e}")
            return False

    def search(
        self,
        query: str,
        k: int = 5,
        mode: str = "hybrid",
    ) -> List[Dict]:
        """Search documents in Memvid.

        Args:
            query: Search query string
            k: Number of results to return
            mode: Search mode - "lex" (lexical), "sem" (semantic), or "hybrid"

        Returns:
            List of search result dictionaries
        """
        try:
            results = self.mem.find(
                query=query,
                k=k,
                mode=mode,
            )
            logger.info(
                f"Search completed for query: '{query}' - found {len(results)} results"
            )
            return results
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

    def enrich_entities(self) -> bool:
        """Extract and enrich entities from all documents.

        This process identifies entities (people, organizations, concepts, etc.)
        and builds an O(1) lookup index for fast querying.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting entity enrichment...")
            self.mem.enrich(engine="rules")
            logger.success("Entity enrichment completed")
            return True
        except Exception as e:
            logger.error(f"Entity enrichment failed: {e}")
            return False

    def get_entity_state(self, entity_name: str) -> Optional[Dict]:
        """Get entity state (O(1) lookup).

        Args:
            entity_name: Name of the entity to query

        Returns:
            Entity state dictionary or None if not found
        """
        try:
            result = self.mem.get_state(entity_name)
            return result
        except Exception as e:
            logger.error(f"Failed to get entity state '{entity_name}': {e}")
            return None

    def get_stats(self) -> Dict:
        """Get Memvid store statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            stats = {
                "file_path": self.memvid_path,
                "file_size_bytes": os.path.getsize(self.memvid_path)
                if os.path.exists(self.memvid_path)
                else 0,
                "file_size_mb": round(
                    os.path.getsize(self.memvid_path) / (1024 * 1024), 2
                )
                if os.path.exists(self.memvid_path)
                else 0,
                "index_kind": settings.memvid_index_kind,
                "initialized": self.mem is not None,
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "file_path": self.memvid_path,
                "file_size_bytes": 0,
                "file_size_mb": 0,
                "index_kind": settings.memvid_index_kind,
                "initialized": False,
            }

    async def count_documents(self) -> int:
        """Count total number of documents in Memvid.

        Returns:
            Number of documents
        """
        try:
            # Perform a search with empty query to get all docs
            results = self.mem.find(query="", k=1000)
            return len(results)
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0

    def clear_all(self) -> bool:
        """Clear all documents from Memvid.

        Warning: This is destructive and cannot be undone.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the file and reinitialize
            if os.path.exists(self.memvid_path):
                os.remove(self.memvid_path)
                logger.warning(f"Deleted Memvid store: {self.memvid_path}")

            # Reinitialize
            self._initialize()
            logger.success("Memvid cleared and reinitialized")
            return True
        except Exception as e:
            logger.error(f"Failed to clear Memvid: {e}")
            return False


# Global singleton instance
memvid = MemvidService()
