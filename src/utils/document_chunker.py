"""Document chunking utility for splitting large documents into embeddable chunks."""

import re
from typing import Any

from loguru import logger

# Maximum chunk size in characters (roughly 2500 tokens, leaving buffer)
# Using ~4 chars per token as a conservative estimate
MAX_CHUNK_SIZE = 10000  # ~2500 tokens
CHUNK_OVERLAP = 250  # Overlap between chunks to preserve context


def chunk_document(
    content: str, doc_id: str, metadata: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Split a large document into smaller chunks for embedding.

    Args:
        content: The document content to chunk
        doc_id: Base document ID
        metadata: Base metadata for the document

    Returns:
        List of chunked documents with unique IDs
    """
    if len(content) <= MAX_CHUNK_SIZE:
        # Document is small enough, return as-is
        return [
            {
                "id": doc_id,
                "content": content,
                "metadata": metadata,
            }
        ]

    chunks = []
    # Try to split by markdown headers first (preserves semantic structure)
    sections = re.split(r"\n(?=#{1,6}\s)", content)

    # Filter out empty sections
    sections = [s.strip() for s in sections if s.strip()]

    current_chunk = ""
    chunk_index = 0

    for section in sections:
        # If adding this section would exceed max size, finalize current chunk
        if current_chunk and len(current_chunk) + len(section) > MAX_CHUNK_SIZE:
            if current_chunk.strip():
                chunks.append(
                    _create_chunk(doc_id, current_chunk.strip(), metadata, chunk_index)
                )
                chunk_index += 1

            # Start new chunk with overlap from previous chunk
            if CHUNK_OVERLAP > 0 and current_chunk:
                overlap_text = current_chunk[-CHUNK_OVERLAP:]
                current_chunk = overlap_text + "\n\n" + section
            else:
                current_chunk = section
        else:
            # Add section to current chunk
            if current_chunk:
                current_chunk += "\n\n" + section
            else:
                current_chunk = section

        # If current chunk itself is too large, split by paragraphs
        while len(current_chunk) > MAX_CHUNK_SIZE:
            current_chunk = _split_by_paragraphs(
                current_chunk, doc_id, metadata, chunks, chunk_index
            )
            chunk_index = len(chunks)

    # Add final chunk
    if current_chunk.strip():
        chunks.append(
            _create_chunk(doc_id, current_chunk.strip(), metadata, chunk_index)
        )

    # Update total_chunks in all metadata
    total_chunks = len(chunks)
    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = total_chunks

    logger.info(
        f"✓ Chunked document {doc_id}: {len(content)} chars → {total_chunks} chunks "
        f"(avg {len(content) // total_chunks} chars/chunk)"
    )

    return chunks


def _create_chunk(
    doc_id: str, content: str, metadata: dict[str, Any], chunk_index: int
) -> dict[str, Any]:
    """Create a chunk dictionary."""
    return {
        "id": f"{doc_id}_chunk_{chunk_index}",
        "content": content,
        "metadata": {
            **metadata,
            "chunk_index": chunk_index,
            "total_chunks": None,  # Will be set later
        },
    }


def _split_by_paragraphs(
    text: str,
    doc_id: str,
    metadata: dict[str, Any],
    chunks: list[dict[str, Any]],
    chunk_index: int,
) -> str:
    """Split text by paragraphs and add chunks, returning remaining text."""
    paragraphs = text.split("\n\n")
    temp_chunk = ""

    for para in paragraphs:
        if len(temp_chunk) + len(para) + 2 > MAX_CHUNK_SIZE:
            if temp_chunk.strip():
                chunks.append(
                    _create_chunk(doc_id, temp_chunk.strip(), metadata, chunk_index)
                )
                chunk_index += 1

            # Start new chunk with overlap
            if CHUNK_OVERLAP > 0 and temp_chunk:
                overlap_text = temp_chunk[-CHUNK_OVERLAP:]
                temp_chunk = overlap_text + "\n\n" + para
            else:
                temp_chunk = para
        else:
            if temp_chunk:
                temp_chunk += "\n\n" + para
            else:
                temp_chunk = para

    return temp_chunk
