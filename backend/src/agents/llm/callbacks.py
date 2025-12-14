"""LangSmith and logging callbacks for observability."""

import structlog
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from typing import Any

logger = structlog.get_logger(__name__)


class StructuredLoggingCallback(BaseCallbackHandler):
    """Callback handler for structured logging of LLM interactions."""

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        """Log when LLM starts processing."""
        logger.info(
            "llm_start",
            session_id=self.session_id,
            model=serialized.get("name", "unknown"),
            prompt_count=len(prompts),
        )

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Log when LLM completes processing."""
        total_tokens = 0
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            total_tokens = token_usage.get("total_tokens", 0)

        logger.info(
            "llm_end",
            session_id=self.session_id,
            generations_count=len(response.generations),
            total_tokens=total_tokens,
        )

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Log LLM errors."""
        logger.error(
            "llm_error",
            session_id=self.session_id,
            error=str(error),
            error_type=type(error).__name__,
        )

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Log when a chain starts."""
        logger.debug(
            "chain_start",
            session_id=self.session_id,
            chain_name=serialized.get("name", "unknown"),
        )

    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Log when a chain completes."""
        logger.debug(
            "chain_end",
            session_id=self.session_id,
            output_keys=list(outputs.keys()) if isinstance(outputs, dict) else None,
        )

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Log when a tool starts."""
        logger.info(
            "tool_start",
            session_id=self.session_id,
            tool_name=serialized.get("name", "unknown"),
        )

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Log when a tool completes."""
        logger.info(
            "tool_end",
            session_id=self.session_id,
            output_length=len(output) if output else 0,
        )

    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        """Log agent actions."""
        logger.info(
            "agent_action",
            session_id=self.session_id,
            tool=getattr(action, "tool", "unknown"),
        )


def setup_langsmith_tracing() -> None:
    """Configure LangSmith tracing if enabled."""
    from src.agents.config.settings import get_settings

    settings = get_settings()

    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        import os

        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

        logger.info(
            "langsmith_enabled",
            project=settings.langchain_project,
        )
    else:
        logger.info("langsmith_disabled")
