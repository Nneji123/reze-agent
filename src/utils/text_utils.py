"""Text processing utilities for RAG and prompt building."""

import re
from typing import Optional

import tiktoken
from llmlingua import PromptCompressor
from loguru import logger


class TokenCounter:
    """Utility for counting tokens in text."""

    def __init__(self):
        self._encoder: Optional[tiktoken.Encoding] = None
        try:
            self._encoder = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"tiktoken init failed: {e}")

    def count(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0
        if not self._encoder:
            return len(text) // 4
        try:
            return len(self._encoder.encode(text))
        except Exception:
            return len(text) // 4


class TextSummarizer:
    """Utility for summarizing/compressing text using LLMLingua."""

    def __init__(self):
        self._llm_lingua: Optional[PromptCompressor] = None
        self._token_counter = TokenCounter()
        # Very aggressive compression: 0.3 = 30% of original (70% reduction)
        self._summarization_ratio = 0.3
        # Persona compression: 0.5 = 50% of original (50% reduction)
        self._persona_summarization_ratio = 0.5
        # LLMLingua max sequence length is 512 tokens
        # Use 450 as safe limit to account for tokenization differences
        self._max_tokens = 450
        try:
            self._llm_lingua = PromptCompressor(
                model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
                use_llmlingua2=True,
                device_map="cpu",
            )
            logger.info("LLMLingua compressor initialized")
        except Exception as e:
            logger.warning(f"LLMLingua init failed: {e}")

    def summarize(
        self, text: str, is_persona: bool = False, min_length: int = 100
    ) -> str:
        """
        Summarize text using LLMLingua compression.

        Note: LLMLingua has a max sequence length of 512 tokens, so we chunk large texts.

        Args:
            text: Text to compress
            is_persona: If True, use less aggressive compression for persona documents
            min_length: Minimum text length to attempt summarization

        Returns:
            Summarized text, or original text if summarization fails or text is too short
        """
        if not text or len(text) < min_length:
            return text

        if not self._llm_lingua:
            logger.warning("LLMLingua not initialized, returning original text")
            return text

        try:
            # Check token count first
            tokens = self._token_counter.count(text)

            if tokens <= self._max_tokens:
                # Text is within limit, compress directly
                return self._compress_chunk(text, is_persona)

            # Text exceeds 512 tokens, need to chunk by actual token count
            logger.debug(
                f"Text has {tokens} tokens, chunking for LLMLingua (max {self._max_tokens})"
            )
            chunks = []
            words = text.split()
            current_chunk = []
            current_tokens = 0

            for word in words:
                word_tokens = self._token_counter.count(word)

                # Check if adding this word would exceed limit
                # Recalculate actual token count of current chunk + word to be safe
                test_chunk = " ".join(current_chunk + [word])
                test_tokens = self._token_counter.count(test_chunk)

                if test_tokens > self._max_tokens:
                    # Finalize current chunk
                    if current_chunk:
                        chunk_text = " ".join(current_chunk)
                        # Double-check token count before compressing
                        chunk_tokens = self._token_counter.count(chunk_text)
                        if chunk_tokens > self._max_tokens:
                            logger.warning(
                                f"Chunk has {chunk_tokens} tokens, truncating before compression"
                            )
                            # Truncate aggressively
                            while (
                                chunk_tokens > self._max_tokens and len(chunk_text) > 0
                            ):
                                chunk_text = chunk_text[:-50]
                                chunk_tokens = self._token_counter.count(chunk_text)
                        compressed_chunk = self._compress_chunk(chunk_text, is_persona)
                        chunks.append(compressed_chunk)
                    # Start new chunk with current word
                    current_chunk = [word]
                else:
                    current_chunk.append(word)

            # Add final chunk
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                # Double-check token count before compressing
                chunk_tokens = self._token_counter.count(chunk_text)
                if chunk_tokens > self._max_tokens:
                    logger.warning(
                        f"Final chunk has {chunk_tokens} tokens, truncating before compression"
                    )
                    # Truncate aggressively
                    while chunk_tokens > self._max_tokens and len(chunk_text) > 0:
                        chunk_text = chunk_text[:-50]
                        chunk_tokens = self._token_counter.count(chunk_text)
                compressed_chunk = self._compress_chunk(chunk_text, is_persona)
                chunks.append(compressed_chunk)

            return "\n".join(chunks)
        except Exception as e:
            logger.warning(f"LLMLingua compression failed: {e}")
            return text

    def _compress_chunk(self, text: str, is_persona: bool) -> str:
        """Compress a single chunk of text, ensuring it's within token limit."""
        # Verify token count before compressing - use strict limit
        tokens = self._token_counter.count(text)
        if tokens > self._max_tokens:
            logger.warning(
                f"Chunk has {tokens} tokens (exceeds {self._max_tokens}), truncating..."
            )
            # Truncate character by character until within limit
            # Start with conservative estimate
            max_chars = int(self._max_tokens * 3.5)  # More conservative estimate
            text = text[:max_chars]
            tokens = self._token_counter.count(text)

            # If still too long, truncate more aggressively
            while tokens > self._max_tokens and len(text) > 0:
                # Remove 10% at a time until within limit
                remove_chars = max(1, len(text) // 10)
                text = text[:-remove_chars]
                tokens = self._token_counter.count(text)

            if tokens > self._max_tokens:
                # Last resort: truncate to very small size
                logger.error(
                    f"Could not truncate chunk below {self._max_tokens} tokens, "
                    f"returning empty string"
                )
                return ""

        compression_ratio = (
            self._persona_summarization_ratio
            if is_persona
            else self._summarization_ratio
        )

        try:
            compressed = self._llm_lingua.compress_prompt(
                text,
                rate=compression_ratio,
                force_tokens=["\n", "?", "!"],  # Preserve important punctuation
            )

            # LLMLingua returns a dict with 'compressed_prompt' key
            if isinstance(compressed, dict):
                summary = compressed.get("compressed_prompt", text)
            else:
                summary = compressed

            if summary and len(summary) > 50:
                return summary
            return text
        except Exception as e:
            logger.error(f"Error compressing chunk: {e}")
            # Return truncated text if compression fails
            return (
                text[: self._max_tokens * 4]
                if len(text) > self._max_tokens * 4
                else text
            )


def clean_markdown(text: str) -> str:
    """
    Remove markdown formatting from text for WhatsApp compatibility.

    Args:
        text: Text with markdown formatting

    Returns:
        Text with markdown removed
    """
    if not text:
        return text

    # Bold, italic, code
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)

    # Headers, links, images
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)

    # Lists (with multiline flag)
    text = re.sub(r"^\s*[-*+]\s*", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s*", "• ", text, flags=re.MULTILINE)

    # Multiple newlines
    text = re.sub(r"\n\s*\n", "\n\n", text)

    return text.strip()


def build_user_context(
    phone_number: Optional[str],
    is_registered: bool = True,
    is_whitelisted: bool = False,
) -> str:
    """
    Build user context string for prompts.

    Args:
        phone_number: User's phone number
        is_registered: Whether user is registered
        is_whitelisted: Whether user is whitelisted

    Returns:
        Formatted user context string
    """
    if not phone_number:
        return ""

    registration_status = (
        "registered"
        if is_registered
        else "not registered (can chat but needs to register for errands)"
    )
    whitelist_status = (
        "whitelisted"
        if is_whitelisted
        else "not whitelisted (needs activation code for errands)"
    )

    return (
        f"User: {phone_number} ({registration_status}, {whitelist_status}). "
        f"Use get_user_details for personalization. "
        f"For errands, use {phone_number} as user_phone."
    )


def limit_conversation_context(
    conv_text: str, max_tokens: int, token_counter: TokenCounter
) -> str:
    """
    Limit conversation context to fit within token budget.

    Args:
        conv_text: Full conversation text
        max_tokens: Maximum tokens allowed
        token_counter: TokenCounter instance

    Returns:
        Limited conversation text
    """
    tokens = token_counter.count(conv_text)
    if tokens <= max_tokens:
        return conv_text

    lines = conv_text.split("\n")
    limited = []
    current = 0
    for line in reversed(lines):
        line_tokens = token_counter.count(line)
        if current + line_tokens <= max_tokens:
            limited.insert(0, line)
            current += line_tokens
        else:
            break

    return "\n".join(limited)
