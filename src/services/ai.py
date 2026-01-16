"""AI service with GLM 4.7 integration from z.ai.

This module provides the AI agent powered by GLM 4.7 (z.ai),
which is OpenAI-compatible. It handles both regular and streaming responses.
"""

from typing import Optional

import openai
from loguru import logger
from pydantic_ai import Agent, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo
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

        Returns:
            Configured Agent instance
        """
        try:
            logger.info(
                f"Creating GLM 4.7 agent: {settings.glm_model} "
                f"at {settings.glm_base_url}"
            )

            from pydantic_ai.providers.openai import OpenAIProvider

            from src.services.prompt import REZE_INSTRUCTIONS, REZE_PERSONA

            provider = OpenAIProvider(
                api_key=settings.glm_api_key,
                base_url=settings.glm_base_url,
            )

            model = OpenAIChatModel(
                model_name=settings.glm_model,
                provider=provider,
            )

            logger.info(
                f"OpenAIChatModel created for {settings.glm_model} "
                f"with support for tool calling and streaming"
            )

            logger.info(f"Registering {len(ALL_TOOLS)} tools with agent")
            for tool in ALL_TOOLS:
                logger.info(f"  - Tool: {tool.__name__}")

            agent = Agent(
                model,
                tools=ALL_TOOLS,
                name="reze_agent",
                system_prompt=[REZE_PERSONA, REZE_INSTRUCTIONS],
            )

            logger.success(
                f"GLM 4.7 agent created successfully with {len(ALL_TOOLS)} tools registered"
            )

            self._inspect_tool_schemas(agent)

            logger.info("=== Agent Configuration Inspection ===")
            logger.info(f"Agent name: {agent.name}")
            logger.info(f"Model: {settings.glm_model}")
            logger.info(f"Base URL: {settings.glm_base_url}")
            logger.info(f"Registered tools count: {len(ALL_TOOLS)}")

            if hasattr(agent, "tools") and agent.tools:
                logger.info(
                    f"Tools attribute exists and contains {len(agent.tools)} items"
                )
                for tool_name, tool_func in agent.tools.items():
                    logger.info(f"  - {tool_name}: {tool_func}")
            else:
                logger.warning("No tools attribute found or tools list is empty")

            logger.info("=== End Agent Configuration Inspection ===")

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

            if hasattr(result, "tool_calls") and result.tool_calls:
                logger.info(
                    f"Agent called {len(result.tool_calls)} tools: {[tc.name for tc in result.tool_calls]}"
                )
            else:
                logger.debug("No tools were called in this response")

            logger.info(f"Agent response generated for message length: {len(message)}")
            return result

        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            raise

    async def stream_agent(self, message: str):
        """Run agent with streaming response.

        Args:
            message: User message to process

        Yields:
            Response chunks as they're generated
        """
        try:
            agent = self.get_agent()
            logger.debug(f"Streaming agent with message: '{message[:100]}...'")

            async with agent.run_stream(message) as result:
                async for chunk in result.stream():
                    logger.debug(f"Streamed chunk length: {len(chunk)}")
                    yield chunk

            if hasattr(result, "all_messages"):
                for msg in result.all_messages():
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        logger.info(
                            f"Tools called during streaming: {[tc.name for tc in msg.tool_calls]}"
                        )
            elif hasattr(result, "tool_calls") and result.tool_calls:
                logger.info(
                    f"Agent called {len(result.tool_calls)} tools during streaming: {[tc.name for tc in result.tool_calls]}"
                )
            else:
                logger.debug("No tools were called during streaming")

            logger.info(f"Streaming completed for message length: {len(message)}")

        except Exception as e:
            logger.error(f"Agent streaming failed: {e}")
            raise

    def _inspect_tool_schemas(self, agent: Agent):
        """Inspect and log tool schemas using PydanticAI AgentInfo pattern.

        Args:
            agent: The configured PydanticAI Agent instance
        """
        try:
            logger.info("=== Tool Schema Inspection ===")

            from pydantic_ai import Agent

            if hasattr(agent, "function_tools"):
                tools = agent.function_tools
                logger.info(f"Found {len(tools)} function tools")

                for i, tool in enumerate(tools):
                    logger.info(f"\nTool {i + 1}:")
                    logger.info(f"  Name: {tool.name}")
                    logger.info(f"  Description: {tool.description}")

                    if hasattr(tool, "parameters_json_schema"):
                        logger.info(f"  Parameters:")
                        schema = tool.parameters_json_schema
                        if schema and "properties" in schema:
                            for param_name, param_info in schema["properties"].items():
                                param_type = param_info.get("type", "unknown")
                                param_desc = param_info.get("description", "")
                                required = (
                                    "required"
                                    if param_name in schema.get("required", [])
                                    else "optional"
                                )
                                logger.info(
                                    f"    - {param_name} ({param_type}, {required}): {param_desc}"
                                )
                            else:
                                logger.info("    No parameters")

            logger.info("=== End Tool Schema Inspection ===")

        except Exception as e:
            logger.error(f"Failed to inspect tool schemas: {e}", exc_info=True)


# Global AI service singleton instance
ai_service = AIService()
