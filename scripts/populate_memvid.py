"""Script to populate Memvid with Resend.com documentation.

This script fetches documentation from Resend.com URLs, parses them,
and stores them in Memvid for RAG (Retrieval-Augmented Generation).
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from memvid_sdk import create, use

from src.config import settings


class MemvidPopulator:
    """Populates Memvid with documentation."""

    def __init__(self):
        self.memvid_path = settings.memvid_file_path
        self.mem = None
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Mozilla/5.0 (Reze AI Agent)"},
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def initialize_memvid(self):
        """Initialize or load Memvid store."""
        logger.info(f"Initializing Memvid at {self.memvid_path}")

        if os.path.exists(self.memvid_path):
            logger.info("Loading existing Memvid store")
            self.mem = use(
                kind=settings.memvid_index_kind,
                filename=self.memvid_path,
                enable_lex=True,
                enable_vec=False,
                mode="open",
            )
        else:
            logger.info("Creating new Memvid store")
            self.mem = create(
                filename=self.memvid_path,
                kind=settings.memvid_index_kind,
                enable_lex=True,
                enable_vec=False,
            )

    async def fetch_page(self, url: str) -> str:
        """Fetch a single page from URL."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return ""

    def parse_html(self, html: str, url: str) -> Dict[str, str]:
        """Parse HTML and extract content."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        # Extract title
        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # Extract main content
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_=lambda x: x and "content" in str(x).lower())
            or soup.find("body")
        )

        if not main_content:
            return {"title": title, "content": "", "url": url}

        # Clean up text
        text = main_content.get_text(separator="\n", strip=True)
        lines = [
            line.strip() for line in text.split("\n") if line.strip() and len(line) > 10
        ]
        content = "\n".join(lines)

        return {"title": title, "content": content, "url": url}

    def add_to_memvid(self, title: str, content: str, url: str) -> bool:
        """Add document to Memvid."""
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
            return True
        except Exception as e:
            logger.error(f"Failed to add {title}: {e}")
            return False

    async def fetch_and_store(self, url: str) -> bool:
        """Fetch URL and store in Memvid."""
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

    async def load_sitemap_from_file(self) -> List[str]:
        """Load all documentation URLs from local sitemap.xml file."""
        try:
            sitemap_path = Path(__file__).parent / "sitemap.xml"
            logger.info(f"Loading sitemap from {sitemap_path}")

            with open(sitemap_path, "r", encoding="utf-8") as f:
                sitemap_text = f.read()

            # Split by whitespace and filter for URLs
            tokens = sitemap_text.split()
            urls = [token for token in tokens if token.startswith("https://")]

            logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls

        except Exception as e:
            logger.error(f"Failed to load sitemap: {e}")
            return []

    async def populate_from_sitemap(
        self, max_urls: int = None, concurrency: int = 10
    ) -> int:
        """Populate Memvid using URLs from sitemap with concurrent processing.

        Args:
            max_urls: Maximum number of URLs to process (None = all)
            concurrency: Number of concurrent fetches (default: 10)

        Returns:
            Number of successfully added documents
        """
        logger.info("📋 Loading documentation URLs from sitemap...")
        urls = await self.load_sitemap_from_file()

        if max_urls:
            urls = urls[:max_urls]
            logger.info(f"Limited to {max_urls} URLs")

        total = len(urls)
        success_count = 0

        # Process URLs in batches with concurrency control
        logger.info(f"Processing {total} URLs with concurrency={concurrency}")

        for i in range(0, total, concurrency):
            batch = urls[i : i + concurrency]
            batch_num = i // concurrency + 1
            total_batches = (total + concurrency - 1) // concurrency

            logger.info(
                f"Batch {batch_num}/{total_batches}: Processing {len(batch)} URLs"
            )

            # Fetch and store concurrently
            results = await asyncio.gather(
                *[self.fetch_and_store(url) for url in batch],
                return_exceptions=True,
            )

            # Count successes
            for result in results:
                if isinstance(result, bool) and result:
                    success_count += 1
                elif isinstance(result, Exception):
                    logger.error(f"Exception in batch: {result}")

            # Small delay between batches
            if i + concurrency < total:
                await asyncio.sleep(0.5)

        logger.success(f"Population complete! Added {success_count}/{total} documents")
        return success_count

    async def get_stats(self) -> Dict:
        """Get Memvid statistics."""
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

    async def close(self):
        """Close resources."""
        await self.client.aclose()


async def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("Reze AI Agent - Memvid Population Script")
    logger.info("=" * 80)

    populator = MemvidPopulator()

    try:
        await populator.initialize_memvid()
        await populator.get_stats()

        logger.info("\n📚 Populating Memvid with Resend.com documentation...")
        await populator.populate_from_sitemap(
            max_urls=None,  # Set to a number to limit (e.g., 50)
            concurrency=10,  # Adjust based on your needs
        )

        logger.info("\n📊 Final statistics:")
        await populator.get_stats()

        logger.info("\n🔍 Enriching entities...")
        try:
            populator.mem.enrich(engine="rules")
            logger.success("Entity enrichment complete")
        except Exception as e:
            logger.warning(f"Entity enrichment failed (non-critical): {e}")

        logger.success("\n✅ Memvid population complete!")
        logger.info(f"📁 Knowledge base saved to: {populator.memvid_path}")

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error during population: {e}", exc_info=True)
    finally:
        await populator.close()

    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
