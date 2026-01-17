"""Script to populate Memvid with Resend.com documentation.

This script fetches documentation from Resend.com URLs, parses them,
and stores them in Memvid for RAG (Retrieval-Augmented Generation).
"""

import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from memvid_sdk import create, use

from src.config import settings


class MemvidPopulator:
    """Populates Memvid with documentation."""

    def __init__(self):
        self.memvid_path: str = settings.memvid_file_path
        self.backup_path: str = self.memvid_path + ".backup"
        self.mem = None
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Mozilla/5.0 (Reze AI Agent)"},
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def initialize_memvid(self) -> None:
        """Initialize or load Memvid store."""
        logger.info(f"Initializing Memvid at {self.memvid_path}")

        if os.path.exists(self.memvid_path):
            logger.info("Loading existing Memvid store")

            self._create_backup()

            try:
                self.mem = use(
                    kind=settings.memvid_index_kind,
                    filename=self.memvid_path,
                    enable_lex=True,
                    enable_vec=False,
                    mode="open",
                )
                logger.info("Memvid store loaded successfully")
            except Exception as load_error:
                error_msg = str(load_error)
                logger.error(f"Failed to load Memvid store: {error_msg}")

                is_corruption = any(
                    keyword in error_msg.lower()
                    for keyword in [
                        "sketch track",
                        "tantivy",
                        "invalid",
                        "corrupted",
                    ]
                )

                if is_corruption:
                    logger.warning(
                        "Detected Memvid file corruption, attempting recovery..."
                    )
                    if self._attempt_recovery():
                        logger.success("Memvid recovered successfully")
                        return
                    else:
                        logger.warning("Recovery failed, creating fresh store...")

                raise
        else:
            logger.info("Creating new Memvid store")
            self.mem = create(
                filename=self.memvid_path,
                kind=settings.memvid_index_kind,
                enable_lex=True,
                enable_vec=False,
            )

    async def fetch_page(self, url: str) -> str:
        """Fetch a single page from URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content or empty string on failure
        """
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return ""

    def parse_html(self, html: str, url: str) -> dict[str, str]:
        """Parse HTML and extract content.

        Args:
            html: HTML content
            url: Source URL

        Returns:
            Dictionary with title, content, and url
        """
        soup = BeautifulSoup(html, "html.parser")

        for element in soup(["script", "style"]):
            element.decompose()

        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_=lambda x: x and "content" in str(x).lower())
            or soup.find("body")
        )

        if not main_content:
            return {"title": title, "content": "", "url": url}

        text = main_content.get_text(separator="\n", strip=True)
        lines = [
            line.strip() for line in text.split("\n") if line.strip() and len(line) > 10
        ]
        content = "\n".join(lines)

        return {"title": title, "content": content, "url": url}

    def add_to_memvid(self, title: str, content: str, url: str) -> bool:
        """Add document to Memvid.

        Args:
            title: Document title
            content: Document content
            url: Source URL

        Returns:
            True if successful, False otherwise
        """
        try:
            self._create_backup()

            self.mem.put(
                title=title,
                text=content,
                metadata={
                    "url": url,
                    "source": "resend.com/docs",
                    "length": len(content),
                },
            )
            return True
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to add {title}: {e}")

            is_corruption = any(
                keyword in error_msg.lower()
                for keyword in ["tantivy", "index writer", "sketch track", "invalid"]
            )

            if is_corruption:
                logger.warning(
                    "Detected corruption during add_to_memvid, attempting recovery..."
                )
                if self._attempt_recovery():
                    try:
                        self.mem.put(
                            title=title,
                            text=content,
                            metadata={
                                "url": url,
                                "source": "resend.com/docs",
                                "length": len(content),
                            },
                        )
                        logger.info(f"Document added after recovery: {title}")
                        return True
                    except Exception as retry_error:
                        logger.error(f"Retry failed: {retry_error}")

            return False

    async def fetch_and_store(self, url: str) -> bool:
        """Fetch URL and store in Memvid.

        Args:
            url: URL to fetch and store

        Returns:
            True if successful, False otherwise
        """
        html = await self.fetch_page(url)
        if not html:
            return False

        parsed = self.parse_html(html, url)

        if not parsed["content"] or len(parsed["content"]) < 100:
            logger.warning(f"Skipping {url} - insufficient content")
            return False

        success = self.add_to_memvid(
            title=parsed["title"],
            content=parsed["content"],
            url=parsed["url"],
        )

        if success:
            logger.success(f"Added: {parsed['title']}")

        return success

    async def load_sitemap_from_file(self) -> list[str]:
        """Load all documentation URLs from local sitemap.xml file.

        Returns:
            List of URLs from sitemap
        """
        try:
            sitemap_path = Path(__file__).parent / "sitemap.xml"
            logger.info(f"Loading sitemap from {sitemap_path}")

            with open(sitemap_path, "r", encoding="utf-8") as f:
                sitemap_text = f.read()

            tokens = sitemap_text.split()
            urls = [token for token in tokens if token.startswith("https://")]

            logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls
        except Exception as e:
            logger.error(f"Failed to load sitemap: {e}")
            return []

    async def populate_from_sitemap(
        self, max_urls: int | None = None, concurrency: int = 10
    ) -> int:
        """Populate Memvid using URLs from sitemap with concurrent processing.

        Args:
            max_urls: Maximum number of URLs to process (None = all)
            concurrency: Number of concurrent fetches (default: 10)

        Returns:
            Number of successfully added documents
        """
        logger.info("Loading documentation URLs from sitemap...")
        urls = await self.load_sitemap_from_file()

        if max_urls:
            urls = urls[:max_urls]
            logger.info(f"Limited to {max_urls} URLs")

        total = len(urls)
        success_count = 0

        logger.info(f"Processing {total} URLs with concurrency={concurrency}")

        for i in range(0, total, concurrency):
            batch = urls[i : i + concurrency]
            batch_num = i // concurrency + 1
            total_batches = (total + concurrency - 1) // concurrency

            logger.info(
                f"Batch {batch_num}/{total_batches}: Processing {len(batch)} URLs"
            )

            results = await asyncio.gather(
                *[self.fetch_and_store(url) for url in batch],
                return_exceptions=True,
            )

            for result in results:
                if isinstance(result, bool) and result:
                    success_count += 1
                elif isinstance(result, Exception):
                    logger.error(f"Exception in batch: {result}")

            if i + concurrency < total:
                await asyncio.sleep(0.5)

        logger.success(f"Population complete! Added {success_count}/{total} documents")
        return success_count

    async def get_stats(self) -> dict[str, Any]:
        """Get Memvid statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            file_size = (
                os.path.getsize(self.memvid_path)
                if os.path.exists(self.memvid_path)
                else 0
            )
            stats = {
                "file_path": self.memvid_path,
                "file_size": file_size,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
            }
            logger.info(f"Memvid stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    async def close(self) -> None:
        """Close resources."""
        await self.client.aclose()

    def _create_backup(self) -> None:
        """Create a backup of Memvid file."""
        try:
            if os.path.exists(self.memvid_path):
                shutil.copy2(self.memvid_path, self.backup_path)
                logger.debug(f"Created backup at: {self.backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    def _attempt_recovery(self) -> bool:
        """Attempt to recover from corrupted Memvid file.

        Returns:
            True if recovery successful, False otherwise
        """
        try:
            if os.path.exists(self.backup_path):
                logger.info("Attempting to restore from backup...")
                shutil.copy2(self.backup_path, self.memvid_path)

                try:
                    self.mem = use(
                        kind=settings.memvid_index_kind,
                        filename=self.memvid_path,
                        enable_lex=True,
                        enable_vec=False,
                        mode="open",
                    )
                    logger.success("Successfully restored from backup")
                    return True
                except Exception as e:
                    logger.error(f"Backup also corrupted: {e}")
                    return False

            logger.warning("No valid backup found, creating fresh Memvid store...")
            if os.path.exists(self.memvid_path):
                os.remove(self.memvid_path)
                logger.info(f"Removed corrupted file: {self.memvid_path}")

            self.mem = create(
                filename=self.memvid_path,
                kind=settings.memvid_index_kind,
                enable_lex=True,
                enable_vec=False,
            )
            logger.success("Created fresh Memvid store")
            return True
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            return False


async def main() -> None:
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("Reze AI Agent - Memvid Population Script")
    logger.info("=" * 80)

    populator = MemvidPopulator()

    try:
        await populator.initialize_memvid()
        await populator.get_stats()

        logger.info("Populating Memvid with Resend.com documentation...")
        await populator.populate_from_sitemap(
            max_urls=None,
            concurrency=10,
        )

        logger.info("Final statistics:")
        await populator.get_stats()

        logger.info("Enriching entities...")
        try:
            populator.mem.enrich(engine="rules")
            logger.success("Entity enrichment complete")
        except Exception as e:
            logger.warning(f"Entity enrichment failed (non-critical): {e}")

        logger.success("Memvid population complete!")
        logger.info(f"Knowledge base saved to: {populator.memvid_path}")
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
    except Exception as e:
        logger.error(f"Error during population: {e}", exc_info=True)
    finally:
        await populator.close()

    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
