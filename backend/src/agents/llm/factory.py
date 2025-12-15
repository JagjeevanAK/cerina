"""LLM factory for creating language model instances."""

from typing import Any, Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from src.agents.config.settings import Settings, get_settings


def get_llm(
    settings: Settings | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Get a language model instance based on configuration.

    Args:
        settings: Application settings (uses default if not provided)
        temperature: Model temperature for response randomness
        **kwargs: Additional arguments passed to the model

    Returns:
        Configured language model instance
    """
    settings = settings or get_settings()

    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=4096,
            **kwargs,
        )
    elif settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
            **kwargs,
        )
    elif settings.llm_provider == "openrouter":
        from langchain_openai import ChatOpenAI

        default_headers = {
            "HTTP-Referer": settings.openrouter_site_url or "https://github.com/cerina",
            "X-Title": settings.openrouter_app_name,
        }

        return ChatOpenAI(
            model=settings.openrouter_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=temperature,
            default_headers=default_headers,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


def get_llm_with_tools(
    tools: Sequence[BaseTool],
    settings: Settings | None = None,
    temperature: float = 0.7,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Get a language model instance with tools bound.

    Args:
        tools: Sequence of tools to bind to the model
        settings: Application settings (uses default if not provided)
        temperature: Model temperature for response randomness
        **kwargs: Additional arguments passed to the model

    Returns:
        Configured language model with tools bound
    """
    llm = get_llm(settings=settings, temperature=temperature, **kwargs)
    return llm.bind_tools(tools)
