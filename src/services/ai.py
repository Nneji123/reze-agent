"""AI service with GLM 4.7 integration from z.ai.

This module provides the AI agent powered by GLM 4.7 (z.ai),
which is OpenAI-compatible. It handles both regular and streaming responses.
"""

from typing import Optional

import openai
from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from src.config import settings
from src.tools import ALL_TOOLS


class AIService:
    """Service for managing AI agent with GLM 4.7."""

    def __init__(self):
        """Initialize AI service."""
        self._agent: Optional[Agent] = None
        self._current_model: Optional[str] = None

    def get_agent(self) -> Agent:
        """Get the configured AI agent.

        Creates or reuses the agent based on current settings.

        Returns:
            Configured Agent instance
        """
        model_key = f"{settings.glm_model}@{settings.glm_base_url}"

        if self._agent is None or self._current_model != model_key:
            self._agent = self._create_agent()
            self._current_model = model_key
            logger.info(f"AI agent ready: {settings.glm_model}")

        return self._agent

    def _create_agent(self) -> Agent:
        """Create GLM 4.7 agent with OpenAI-compatible protocol.

        GLM 4.7 from z.ai uses the OpenAI API format, so we can use
        OpenAIChatModel with custom base_url and api_key.

        Returns:
            Configured Agent instance
        """
        try:
            logger.info(
                f"Creating GLM 4.7 agent: {settings.glm_model} "
                f"at {settings.glm_base_url}"
            )

            # Create OpenAI-compatible provider with custom settings
            from pydantic_ai.providers.openai import OpenAIProvider

            provider = OpenAIProvider(
                api_key=settings.glm_api_key,
                base_url=settings.glm_base_url,
            )

            # Create model with the custom provider
            model = OpenAIChatModel(
                model_name=settings.glm_model,
                provider=provider,
            )

            # Create agent with model, tools, and system prompt
            from src.prompts import REZE_INSTRUCTIONS, REZE_PERSONA

            agent = Agent(
                model,
                tools=ALL_TOOLS,
                name="reze_agent",
                system_prompt=[REZE_PERSONA, REZE_INSTRUCTIONS],
            )

            logger.success("GLM 4.7 agent created successfully")
            return agent

        except Exception as e:
            logger.error(f"Failed to create GLM 4.7 agent: {e}")
            raise

    async def run_agent(self, message: str):
        """Run agent with a message (non-streaming).

        Args:
            message: User message to process

        Returns:
            Agent response data
        """
        try:
            agent = self.get_agent()
            result = await agent.run(message)

            logger.info(f"Agent response generated for message length: {len(message)}")
            return result

        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            raise

    async def stream_agent(self, message: str):
        """Run agent with streaming response.

        This yields chunks of the response as they're generated,
        providing real-time feedback to the user.

        Args:
            message: User message to process

        Yields:
            Response chunks as they're generated
        """
        try:
            agent = self.get_agent()

            async with agent.run_stream(message) as result:
                async for chunk in result.stream():
                    logger.debug(f"Streamed chunk length: {len(chunk)}")
                    yield chunk

            logger.info(f"Streaming completed for message length: {len(message)}")

        except Exception as e:
            logger.error(f"Agent streaming failed: {e}")
            raise


# Global AI service singleton instance
ai_service = AIService()
