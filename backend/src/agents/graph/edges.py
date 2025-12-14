"""Edge and routing logic for the LangGraph workflow."""

from typing import Literal

import structlog

from src.agents.state.graph_state import GraphState

logger = structlog.get_logger(__name__)


def supervisor_router(
    state: GraphState,
) -> Literal[
    "draftsman",
    "safety_guardian",
    "clinical_critic",
    "finalizer",
    "human_review",
    "end",
]:
    """
    Determine the next node based on current state.

    This is the main routing function used by the supervisor pattern.
    """
    stage = state.get("workflow_stage", "initializing")
    quality_metrics = state.get("quality_metrics", {})
    iteration = state.get("iteration_count", 0)
    max_iterations = quality_metrics.get("max_iterations", 5)

    safety = quality_metrics.get("safety", {})
    empathy = quality_metrics.get("empathy", {})

    thread_id = state.get("thread_id", "unknown")

    # Initial state - start with drafting
    if stage == "initializing":
        logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="draftsman", reason="Initial state - starting draft")
        return "draftsman"

    # After safety review
    elif stage == "safety_review":
        if not safety.get("passed", False):
            if iteration >= max_iterations:
                logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="human_review", reason=f"Safety failed, max iterations ({max_iterations}) reached")
                return "human_review"
            logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="draftsman", reason=f"Safety failed, revision needed (iteration {iteration}/{max_iterations})")
            return "draftsman"
        logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="clinical_critic", reason="Safety passed")
        return "clinical_critic"

    # After clinical review
    elif stage == "clinical_review":
        if not empathy.get("passed", False):
            if iteration >= max_iterations:
                logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="human_review", reason=f"Empathy failed, max iterations ({max_iterations}) reached")
                return "human_review"
            logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="draftsman", reason=f"Empathy failed, revision needed (iteration {iteration}/{max_iterations})")
            return "draftsman"
        logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="finalizer", reason="Both safety and empathy passed")
        return "finalizer"

    # Revision stage - route back to safety review
    elif stage == "revising":
        logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="safety_guardian", reason="Revision complete, re-checking safety")
        return "safety_guardian"

    # After finalization - human review
    elif stage == "finalizing":
        logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="human_review", reason="Finalization complete, awaiting human review")
        return "human_review"

    # Human review outcomes
    elif stage == "human_review":
        human_review = state.get("human_review", {})
        decision = human_review.get("decision")

        if decision == "approve":
            logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="end", reason="Human approved - workflow complete")
            return "end"
        elif decision == "reject":
            logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="end", reason="Human rejected - workflow complete")
            return "end"
        elif decision == "edit":
            logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="safety_guardian", reason="Human made edits - re-reviewing")
            return "safety_guardian"
        logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="human_review", reason="Awaiting human decision")
        return "human_review"

    # Terminal states
    elif stage in ["approved", "rejected"]:
        logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="end", reason=f"Terminal state: {stage}")
        return "end"

    # Default - go to human review for safety
    logger.info("routing_decision", thread_id=thread_id, from_stage=stage, to_node="human_review", reason="Default routing for safety")
    return "human_review"


def should_continue(state: GraphState) -> Literal["continue", "end"]:
    """Check if the workflow should continue or end."""
    stage = state.get("workflow_stage", "initializing")
    thread_id = state.get("thread_id", "unknown")

    # End conditions
    if stage in ["approved", "rejected"]:
        logger.debug("should_continue", thread_id=thread_id, decision="end", reason=f"Terminal stage: {stage}")
        return "end"

    # Check if awaiting human input (will be handled by interrupt)
    if state.get("awaiting_human_input", False):
        logger.debug("should_continue", thread_id=thread_id, decision="end", reason="Awaiting human input")
        return "end"

    logger.debug("should_continue", thread_id=thread_id, decision="continue", reason=f"Stage: {stage}")
    return "continue"


def after_draftsman(state: GraphState) -> Literal["safety_guardian"]:
    """Route after draftsman - always goes to safety review."""
    thread_id = state.get("thread_id", "unknown")
    logger.info(
        "edge_routing",
        thread_id=thread_id,
        from_node="draftsman",
        to_node="safety_guardian",
        reason="Draft complete - proceeding to safety review",
    )
    return "safety_guardian"


def after_safety(
    state: GraphState,
) -> Literal["clinical_critic", "draftsman", "human_review"]:
    """Route after safety review."""
    thread_id = state.get("thread_id", "unknown")
    quality_metrics = state.get("quality_metrics", {})
    safety = quality_metrics.get("safety", {})
    iteration = state.get("iteration_count", 0)
    max_iterations = quality_metrics.get("max_iterations", 5)

    if not safety.get("passed", False):
        if iteration >= max_iterations:
            logger.info(
                "edge_routing",
                thread_id=thread_id,
                from_node="safety_guardian",
                to_node="human_review",
                reason=f"SAFETY FAILED - Max iterations ({max_iterations}) reached, escalating to human",
                safety_score=safety.get("overall_safety_score", 0),
            )
            return "human_review"
        logger.info(
            "edge_routing",
            thread_id=thread_id,
            from_node="safety_guardian",
            to_node="draftsman",
            reason=f"SAFETY FAILED - Sending back for revision (iteration {iteration + 1}/{max_iterations})",
            safety_score=safety.get("overall_safety_score", 0),
        )
        return "draftsman"

    logger.info(
        "edge_routing",
        thread_id=thread_id,
        from_node="safety_guardian",
        to_node="clinical_critic",
        reason="SAFETY PASSED - Proceeding to clinical review",
        safety_score=safety.get("overall_safety_score", 0),
    )
    return "clinical_critic"


def after_clinical(
    state: GraphState,
) -> Literal["finalizer", "draftsman", "human_review"]:
    """Route after clinical review."""
    thread_id = state.get("thread_id", "unknown")
    quality_metrics = state.get("quality_metrics", {})
    empathy = quality_metrics.get("empathy", {})
    iteration = state.get("iteration_count", 0)
    max_iterations = quality_metrics.get("max_iterations", 5)

    if not empathy.get("passed", False):
        if iteration >= max_iterations:
            logger.info(
                "edge_routing",
                thread_id=thread_id,
                from_node="clinical_critic",
                to_node="human_review",
                reason=f"EMPATHY FAILED - Max iterations ({max_iterations}) reached, escalating to human",
                empathy_score=empathy.get("overall_empathy_score", 0),
            )
            return "human_review"
        logger.info(
            "edge_routing",
            thread_id=thread_id,
            from_node="clinical_critic",
            to_node="draftsman",
            reason=f"EMPATHY FAILED - Sending back for revision (iteration {iteration + 1}/{max_iterations})",
            empathy_score=empathy.get("overall_empathy_score", 0),
        )
        return "draftsman"

    logger.info(
        "edge_routing",
        thread_id=thread_id,
        from_node="clinical_critic",
        to_node="finalizer",
        reason="EMPATHY PASSED - All reviews complete, proceeding to finalization",
        empathy_score=empathy.get("overall_empathy_score", 0),
    )
    return "finalizer"


def after_finalizer(state: GraphState) -> Literal["human_review"]:
    """Route after finalizer - always goes to human review."""
    thread_id = state.get("thread_id", "unknown")
    logger.info(
        "edge_routing",
        thread_id=thread_id,
        from_node="finalizer",
        to_node="human_review",
        reason="Exercise finalized - awaiting human approval",
    )
    return "human_review"


def after_human_review(
    state: GraphState,
) -> Literal["safety_guardian", "end"]:
    """Route after human review based on decision."""
    thread_id = state.get("thread_id", "unknown")
    human_review = state.get("human_review", {})
    decision = human_review.get("decision")

    if decision == "edit":
        logger.info(
            "edge_routing",
            thread_id=thread_id,
            from_node="human_review",
            to_node="safety_guardian",
            reason="Human made edits - re-running safety review",
        )
        return "safety_guardian"

    logger.info(
        "edge_routing",
        thread_id=thread_id,
        from_node="human_review",
        to_node="end",
        reason=f"Human decision: {decision} - workflow complete",
    )
    return "end"
