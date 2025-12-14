"""Main entry point for the CBT Clinical Review Agent System."""

import asyncio
from typing import Any

from src.agents.config.settings import get_settings
from src.agents.graph.builder import CBTWorkflow
from src.agents.graph.checkpointer import create_checkpointer, close_connection_pool
from src.agents.llm.callbacks import setup_langsmith_tracing
from src.agents.utils.logging import setup_logging, get_logger


async def run_workflow(
    user_input: str,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """
    Run the CBT clinical review workflow.

    Args:
        user_input: The user's request for a CBT exercise
        thread_id: Optional thread ID for persistence

    Returns:
        Final workflow state
    """
    logger = get_logger(__name__)

    async with create_checkpointer() as checkpointer:
        workflow = CBTWorkflow(checkpointer=checkpointer)

        logger.info(
            "workflow_starting",
            user_input=user_input[:100],
            thread_id=thread_id,
        )

        result = await workflow.start(user_input, thread_id)

        logger.info(
            "workflow_complete",
            thread_id=result.get("thread_id"),
            stage=result.get("workflow_stage"),
            iterations=result.get("iteration_count"),
        )

        return result


async def resume_workflow(
    thread_id: str,
    decision: str,
    edits: str | None = None,
    feedback: str | None = None,
    reviewer_id: str | None = None,
) -> dict[str, Any]:
    """
    Resume an interrupted workflow with human input.

    Args:
        thread_id: The thread ID of the interrupted workflow
        decision: "approve", "reject", or "edit"
        edits: Edited content (required for "edit" decision)
        feedback: Optional feedback text
        reviewer_id: Optional reviewer identifier

    Returns:
        Final workflow state
    """
    logger = get_logger(__name__)

    human_decision = {
        "decision": decision,
        "edits": edits,
        "feedback": feedback,
        "reviewer_id": reviewer_id,
    }

    async with create_checkpointer() as checkpointer:
        workflow = CBTWorkflow(checkpointer=checkpointer)

        logger.info(
            "workflow_resuming",
            thread_id=thread_id,
            decision=decision,
        )

        result = await workflow.resume(thread_id, human_decision)

        logger.info(
            "workflow_resumed",
            thread_id=thread_id,
            stage=result.get("workflow_stage"),
        )

        return result


async def get_workflow_state(thread_id: str) -> dict[str, Any] | None:
    """
    Get the current state of a workflow.

    Args:
        thread_id: The thread ID to retrieve state for

    Returns:
        Current state or None if not found
    """
    async with create_checkpointer() as checkpointer:
        workflow = CBTWorkflow(checkpointer=checkpointer)
        return await workflow.get_state(thread_id)


async def main_async() -> None:
    """Async main function for testing."""
    setup_logging()
    setup_langsmith_tracing()

    logger = get_logger(__name__)
    settings = get_settings()

    logger.info(
        "cbt_agent_system_starting",
        llm_provider=settings.llm_provider,
        debug=settings.debug,
    )

    # Example usage
    test_input = "Create an exposure hierarchy for agoraphobia"

    try:
        result = await run_workflow(test_input)
        logger.info(
            "workflow_result",
            stage=result.get("workflow_stage"),
            has_exercise=result.get("final_exercise") is not None,
        )
    except Exception as e:
        logger.error("workflow_error", error=str(e))
        raise
    finally:
        await close_connection_pool()


def main() -> None:
    """Main entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
