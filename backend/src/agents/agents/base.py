"""Base agent class for CBT Clinical Review System."""

from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.config.settings import Settings, get_settings
from src.agents.llm.factory import get_llm
from src.agents.state.graph_state import GraphState

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the CBT Clinical Review System."""

    agent_id: str = "base"
    description: str = "Base agent"

    def __init__(
        self,
        settings: Settings | None = None,
        llm: BaseChatModel | None = None,
        temperature: float = 0.7,
    ):
        """
        Initialize the agent.

        Args:
            settings: Application settings
            llm: Language model instance (created from settings if not provided)
            temperature: Temperature for LLM responses
        """
        self.settings = settings or get_settings()
        self.llm = llm or get_llm(settings=self.settings, temperature=temperature)
        self.temperature = temperature
        self.logger = logger.bind(agent_id=self.agent_id)

    @abstractmethod
    def get_system_prompt(self, state: GraphState) -> str:
        """
        Get the system prompt for this agent.

        Args:
            state: Current graph state

        Returns:
            Formatted system prompt
        """
        pass

    @abstractmethod
    async def process(self, state: GraphState) -> dict[str, Any]:
        """
        Process the current state and return updates.

        Args:
            state: Current graph state

        Returns:
            Dictionary of state updates
        """
        pass

    async def invoke(self, state: GraphState) -> dict[str, Any]:
        """
        Main entry point for agent invocation.

        Args:
            state: Current graph state

        Returns:
            Dictionary of state updates
        """
        self.logger.info(
            "agent_invoke_start",
            session_id=state.get("session_id"),
            workflow_stage=state.get("workflow_stage"),
        )

        try:
            updates = await self.process(state)

            # Add metadata to updates
            updates["current_agent"] = self.agent_id
            updates["updated_at"] = self._get_timestamp()

            self.logger.info(
                "agent_invoke_complete",
                session_id=state.get("session_id"),
                updates_keys=list(updates.keys()),
            )

            return updates

        except Exception as e:
            self.logger.error(
                "agent_invoke_error",
                session_id=state.get("session_id"),
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error_message": f"Agent {self.agent_id} error: {str(e)}",
                "current_agent": self.agent_id,
            }

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list | None = None,
    ) -> str:
        """
        Send a chat message to the LLM.

        Args:
            system_prompt: System prompt for the conversation
            user_message: User message to send
            history: Optional conversation history

        Returns:
            LLM response content
        """
        import time

        messages = [SystemMessage(content=system_prompt)]

        if history:
            messages.extend(history)

        messages.append(HumanMessage(content=user_message))

        self.logger.debug(
            "llm_request_start",
            prompt_length=len(system_prompt),
            message_length=len(user_message),
            history_count=len(history) if history else 0,
        )

        start_time = time.time()
        response = await self.llm.ainvoke(messages)
        elapsed = time.time() - start_time

        if isinstance(response, AIMessage):
            content = response.content
            self.logger.debug(
                "llm_request_complete",
                response_length=len(content),
                elapsed_seconds=round(elapsed, 2),
            )
            return content

        self.logger.debug(
            "llm_request_complete",
            response_length=len(str(response)),
            elapsed_seconds=round(elapsed, 2),
        )
        return str(response)

    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime

        return datetime.utcnow().isoformat()

    def _get_scratchpad(self, state: GraphState) -> dict:
        """Get or initialize this agent's scratchpad in state."""
        scratchpads = state.get("scratchpads", {})
        if self.agent_id not in scratchpads:
            scratchpads[self.agent_id] = {
                "agent_id": self.agent_id,
                "notes": [],
                "last_action": None,
                "iteration_contributions": 0,
            }
        return scratchpads[self.agent_id]

    def _add_note(
        self,
        scratchpad: dict,
        note_type: str,
        content: str,
        severity: str = "info",
        line_reference: int | None = None,
    ) -> dict:
        """Add a note to the scratchpad."""
        note = {
            "agent_id": self.agent_id,
            "timestamp": self._get_timestamp(),
            "note_type": note_type,
            "severity": severity,
            "line_reference": line_reference,
            "content": content,
            "resolved": False,
        }
        scratchpad["notes"].append(note)
        return note
