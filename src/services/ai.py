"""AI service with GLM 4.7 integration from z.ai."""

from typing import Optional

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.config import settings
from src.services.prompt import REZE_INSTRUCTIONS, REZE_PERSONA
from src.tools import ALL_TOOLS


class AIService:
    """Service for managing AI agent with GLM 4.7."""

    def __init__(self):
        self._agent: Optional[Agent] = None
        self._current_model: Optional[str] = None

    def get_agent(self) -> Agent:
        model_key = f"{settings.glm_model}@{settings.glm_base_url}"

        if self._agent is None or self._current_model != model_key:
            self._agent = self._create_agent()
            self._current_model = model_key

        return self._agent

    def _create_agent(self) -> Agent:
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
        agent = self.get_agent()
        return await agent.run(message)

    async def stream_agent(self, message: str):
        agent = self.get_agent()

        async with agent.run_stream(message) as result:
            previous_text = ""

            async for chunk in result.stream():
                if len(chunk) > len(previous_text):
                    delta = chunk[len(previous_text) :]
                    if delta:
                        yield delta
                    previous_text = chunk


# Global singleton instance
ai_service = AIService()
