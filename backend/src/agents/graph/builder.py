"""LangGraph builder for the CBT Clinical Review workflow."""

import time
from typing import Any

import structlog
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph

from src.agents.state.graph_state import GraphState
from src.agents.graph.edges import (
    after_clinical,
    after_draftsman,
    after_finalizer,
    after_human_review,
    after_safety,
)
from src.agents.graph.nodes import (
    clinical_critic_node,
    draftsman_node,
    finalizer_node,
    human_review_node,
    safety_guardian_node,
)

logger = structlog.get_logger(__name__)


def build_graph(
    checkpointer: BaseCheckpointSaver | None = None,
) -> StateGraph:
    """
    Build the CBT Clinical Review workflow graph.

    The graph implements a Supervisor-Worker pattern:
    1. Draftsman creates/revises CBT exercises
    2. Safety Guardian reviews for safety concerns
    3. Clinical Critic evaluates tone and empathy
    4. If reviews fail, loop back to Draftsman
    5. If reviews pass, Finalizer formats the artifact
    6. Human review with interrupt for approval

    Args:
        checkpointer: Optional checkpointer for persistence

    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("draftsman", draftsman_node)
    workflow.add_node("safety_guardian", safety_guardian_node)
    workflow.add_node("clinical_critic", clinical_critic_node)
    workflow.add_node("finalizer", finalizer_node)
    workflow.add_node("human_review", human_review_node)

    workflow.set_entry_point("draftsman")

    workflow.add_conditional_edges(
        "draftsman",
        after_draftsman,
        {
            "safety_guardian": "safety_guardian",
        },
    )

    workflow.add_conditional_edges(
        "safety_guardian",
        after_safety,
        {
            "clinical_critic": "clinical_critic",
            "draftsman": "draftsman",
            "human_review": "human_review",
        },
    )

    workflow.add_conditional_edges(
        "clinical_critic",
        after_clinical,
        {
            "finalizer": "finalizer",
            "draftsman": "draftsman",
            "human_review": "human_review",
        },
    )

    workflow.add_conditional_edges(
        "finalizer",
        after_finalizer,
        {
            "human_review": "human_review",
        },
    )

    workflow.add_conditional_edges(
        "human_review",
        after_human_review,
        {
            "safety_guardian": "safety_guardian",
            "end": END,
        },
    )

    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()


async def create_workflow(
    checkpointer: BaseCheckpointSaver | None = None,
) -> StateGraph:
    """
    Create a workflow instance with optional checkpointer.

    This is a convenience function for creating workflows
    with the default configuration.
    """
    return build_graph(checkpointer=checkpointer)


class CBTWorkflow:
    """
    High-level interface for the CBT Clinical Review workflow.

    This class provides a convenient interface for:
    - Starting new sessions
    - Resuming interrupted sessions
    - Streaming workflow events
    """

    def __init__(self, checkpointer: BaseCheckpointSaver | None = None):
        self.graph = build_graph(checkpointer=checkpointer)
        self.checkpointer = checkpointer
        logger.info(
            "workflow_initialized",
            has_checkpointer=checkpointer is not None,
        )

    async def start(
        self,
        user_input: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Start a new CBT exercise generation workflow.

        Args:
            user_input: The user's request for a CBT exercise
            thread_id: Optional thread ID (generated if not provided)

        Returns:
            Final state after execution (or interrupted state)
        """
        from src.agents.state.graph_state import create_initial_state

        initial_state = create_initial_state(
            user_input=user_input,
            thread_id=thread_id,
        )

        config = {"configurable": {"thread_id": initial_state["thread_id"]}}

        logger.info(
            "workflow_start",
            thread_id=initial_state["thread_id"],
            user_input_preview=user_input[:80] + "..." if len(user_input) > 80 else user_input,
            workflow_flow="Draftsman -> Safety Guardian -> Clinical Critic -> Finalizer -> Human Review",
        )

        start_time = time.time()

        try:
            result = await self.graph.ainvoke(initial_state, config)
            elapsed = time.time() - start_time

            final_stage = result.get("workflow_stage", "unknown")
            logger.info(
                "workflow_paused_or_complete",
                thread_id=initial_state["thread_id"],
                final_stage=final_stage,
                elapsed_seconds=round(elapsed, 2),
                iteration_count=result.get("iteration_count", 0),
                awaiting_human_input=result.get("awaiting_human_input", False),
                status="AWAITING HUMAN REVIEW" if final_stage == "human_review" else final_stage.upper(),
            )

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                "workflow_error",
                thread_id=initial_state["thread_id"],
                error=str(e),
                error_type=type(e).__name__,
                elapsed_seconds=round(elapsed, 2),
            )
            raise

    async def resume(
        self,
        thread_id: str,
        human_decision: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Resume an interrupted workflow with human input.

        Args:
            thread_id: The thread ID of the interrupted workflow
            human_decision: Human review decision with keys:
                - decision: "approve" | "reject" | "edit"
                - edits: Optional edited content (for "edit" decision)
                - feedback: Optional feedback text
                - reviewer_id: Optional reviewer identifier

        Returns:
            Final state after resumption
        """
        from langgraph.types import Command

        config = {"configurable": {"thread_id": thread_id}}

        decision = human_decision.get("decision", "unknown")
        logger.info(
            "workflow_resume",
            thread_id=thread_id,
            decision=decision,
            reviewer_id=human_decision.get("reviewer_id"),
            has_edits=human_decision.get("edits") is not None,
            next_action={
                "approve": "Finalizing and completing workflow",
                "reject": "Marking session as rejected",
                "edit": "Re-running safety and clinical review on edited content",
            }.get(decision, "Processing decision"),
        )

        start_time = time.time()

        try:
            result = await self.graph.ainvoke(
                Command(resume=human_decision),
                config,
            )
            elapsed = time.time() - start_time

            final_stage = result.get("workflow_stage", "unknown")
            logger.info(
                "workflow_resume_complete",
                thread_id=thread_id,
                final_stage=final_stage,
                elapsed_seconds=round(elapsed, 2),
                status="COMPLETED" if final_stage in ("approved", "rejected") else final_stage.upper(),
            )

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                "workflow_resume_error",
                thread_id=thread_id,
                error=str(e),
                error_type=type(e).__name__,
                elapsed_seconds=round(elapsed, 2),
            )
            raise

    async def get_state(self, thread_id: str) -> dict[str, Any] | None:
        """
        Get the current state of a workflow.

        Args:
            thread_id: The thread ID to retrieve state for

        Returns:
            Current state or None if not found
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = await self.graph.aget_state(config)

        if state and state.values:
            logger.debug(
                "workflow_state_retrieved",
                thread_id=thread_id,
                workflow_stage=state.values.get("workflow_stage"),
                iteration_count=state.values.get("iteration_count", 0),
            )
            return state.values

        logger.debug("workflow_state_not_found", thread_id=thread_id)
        return None

    async def stream(
        self,
        user_input: str,
        thread_id: str | None = None,
    ):
        """
        Stream workflow events for real-time updates.

        Args:
            user_input: The user's request for a CBT exercise
            thread_id: Optional thread ID

        Yields:
            Workflow events as they occur
        """
        from src.agents.state.graph_state import create_initial_state

        initial_state = create_initial_state(
            user_input=user_input,
            thread_id=thread_id,
        )

        config = {"configurable": {"thread_id": initial_state["thread_id"]}}

        logger.info(
            "workflow_stream_start",
            thread_id=initial_state["thread_id"],
            user_input_preview=user_input[:50] + "..." if len(user_input) > 50 else user_input,
        )

        event_count = 0
        async for event in self.graph.astream_events(
            initial_state,
            config,
            version="v2",
        ):
            event_count += 1
            yield event

        logger.info(
            "workflow_stream_complete",
            thread_id=initial_state["thread_id"],
            total_events=event_count,
        )
