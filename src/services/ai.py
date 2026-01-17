"""AI service with GLM 4.7 integration from z.ai."""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.config import settings
from src.services.prompt import REZE_INSTRUCTIONS, REZE_PERSONA
from src.tools import ALL_TOOLS


class AIService:
    """Service for managing AI agent with GLM 4.7."""

    def __init__(self):
        """Initialize AI service."""
        self._agent: Agent | None = None
        self._current_model: str | None = None

    def get_agent(self) -> Agent:
        """Get the configured AI agent.

        Returns:
            Configured Agent instance
        """
        model_key = f"{settings.glm_model}@{settings.glm_base_url}"

        if self._agent is None or self._current_model != model_key:
            self._agent = self._create_agent()
            self._current_model = model_key

        return self._agent

    def _create_agent(self) -> Agent:
        """Create GLM 4.7 agent with OpenAI-compatible protocol.

        Returns:
            Configured Agent instance
        """
        provider = OpenAIProvider(
            api_key=settings.glm_api_key,
            base_url=settings.glm_base_url,
        )

        model = OpenAIChatModel(
            model_name=settings.glm_model,
            provider=provider,
        )

        return Agent(
            model,
            tools=ALL_TOOLS,
            name="reze_agent",
            system_prompt=[REZE_PERSONA, REZE_INSTRUCTIONS],
        )

    async def run_agent(self, message: str):
        """Run agent with a message (non-streaming).

        Args:
            message: User message to process

        Returns:
            Agent response data
        """
        agent = self.get_agent()
        return await agent.run(message)

    async def stream_agent(self, message: str):
        """Run agent with streaming response.

        Args:
            message: User message to process

        Yields:
            Response chunks as they're generated
        """
        agent = self.get_agent()

        async with agent.run_stream(message) as result:
            previous_text = ""

            async for chunk in result.stream():
                if len(chunk) > len(previous_text):
                    delta = chunk[len(previous_text) :]
                    if delta:
                        yield delta
                    previous_text = chunk


ai_service = AIService()
