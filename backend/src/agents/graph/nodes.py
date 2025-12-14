"""Node definitions for the LangGraph workflow."""

import time
from typing import Any

import structlog
from langgraph.types import interrupt

from src.agents.agents import (
    ClinicalCriticAgent,
    DraftsmanAgent,
    FinalizerAgent,
    SafetyGuardianAgent,
    SupervisorAgent,
)
from src.agents.config.settings import Settings, get_settings
from src.agents.state.graph_state import GraphState

logger = structlog.get_logger(__name__)

# Singleton agent instances
_agents: dict[str, Any] = {}


def get_agent(agent_type: str, settings: Settings | None = None):
    """Get or create an agent instance."""
    if agent_type not in _agents:
        settings = settings or get_settings()
        agent_classes = {
            "supervisor": SupervisorAgent,
            "draftsman": DraftsmanAgent,
            "safety_guardian": SafetyGuardianAgent,
            "clinical_critic": ClinicalCriticAgent,
            "finalizer": FinalizerAgent,
        }
        if agent_type in agent_classes:
            _agents[agent_type] = agent_classes[agent_type](settings=settings)
            logger.info("agent_created", agent_type=agent_type)
    return _agents.get(agent_type)


async def supervisor_node(state: GraphState) -> dict[str, Any]:
    """Supervisor node - orchestrates the workflow."""
    thread_id = state.get("thread_id", "unknown")
    stage = state.get("workflow_stage", "unknown")
    iteration = state.get("iteration_count", 0)

    logger.info(
        "supervisor_start",
        thread_id=thread_id,
        current_stage=stage,
        iteration=iteration,
        action="Analyzing workflow state and determining next step",
    )

    start_time = time.time()
    agent = get_agent("supervisor")
    result = await agent.invoke(state)
    elapsed = time.time() - start_time

    next_stage = result.get("workflow_stage", stage)
    logger.info(
        "supervisor_complete",
        thread_id=thread_id,
        next_stage=next_stage,
        elapsed_seconds=round(elapsed, 2),
        decision=f"Routing to {next_stage}",
    )

    return result


async def draftsman_node(state: GraphState) -> dict[str, Any]:
    """Draftsman node - creates and revises CBT exercises."""
    thread_id = state.get("thread_id", "unknown")
    user_input = state.get("user_request", {}).get("raw_input", "")[:50]
    draft_version = state.get("draft_history", {}).get("current_version", 0)

    logger.info(
        "draftsman_start",
        thread_id=thread_id,
        draft_version=draft_version,
        user_input_preview=user_input + "..." if len(user_input) == 50 else user_input,
        action="Creating/revising CBT exercise draft",
    )

    start_time = time.time()
    agent = get_agent("draftsman")
    result = await agent.invoke(state)
    elapsed = time.time() - start_time

    new_version = result.get("draft_history", {}).get("current_version", draft_version)
    draft_preview = (result.get("current_draft") or "")[:100]

    logger.info(
        "draftsman_complete",
        thread_id=thread_id,
        new_draft_version=new_version,
        elapsed_seconds=round(elapsed, 2),
        draft_preview=draft_preview + "..." if len(draft_preview) == 100 else draft_preview,
    )

    return result


async def safety_guardian_node(state: GraphState) -> dict[str, Any]:
    """Safety Guardian node - reviews for safety concerns."""
    thread_id = state.get("thread_id", "unknown")
    draft_version = state.get("draft_history", {}).get("current_version", 0)

    logger.info(
        "safety_guardian_start",
        thread_id=thread_id,
        draft_version=draft_version,
        action="Reviewing draft for safety concerns (self-harm risk, medical advice)",
    )

    start_time = time.time()
    agent = get_agent("safety_guardian")
    result = await agent.invoke(state)
    elapsed = time.time() - start_time

    safety = result.get("quality_metrics", {}).get("safety", {})
    safety_score = safety.get("overall_safety_score", 0)
    safety_passed = safety.get("passed", False)

    logger.info(
        "safety_guardian_complete",
        thread_id=thread_id,
        safety_score=safety_score,
        safety_passed=safety_passed,
        self_harm_risk=safety.get("self_harm_risk", 0),
        medical_advice_risk=safety.get("medical_advice_risk", 0),
        elapsed_seconds=round(elapsed, 2),
        result="PASSED" if safety_passed else "FAILED - needs revision",
    )

    return result


async def clinical_critic_node(state: GraphState) -> dict[str, Any]:
    """Clinical Critic node - evaluates tone and empathy."""
    thread_id = state.get("thread_id", "unknown")
    draft_version = state.get("draft_history", {}).get("current_version", 0)

    logger.info(
        "clinical_critic_start",
        thread_id=thread_id,
        draft_version=draft_version,
        action="Evaluating clinical accuracy, tone, and empathy",
    )

    start_time = time.time()
    agent = get_agent("clinical_critic")
    result = await agent.invoke(state)
    elapsed = time.time() - start_time

    empathy = result.get("quality_metrics", {}).get("empathy", {})
    empathy_score = empathy.get("overall_empathy_score", 0)
    empathy_passed = empathy.get("passed", False)

    logger.info(
        "clinical_critic_complete",
        thread_id=thread_id,
        empathy_score=empathy_score,
        empathy_passed=empathy_passed,
        warmth_score=empathy.get("warmth_score", 0),
        clinical_accuracy=empathy.get("clinical_accuracy", 0),
        elapsed_seconds=round(elapsed, 2),
        result="PASSED" if empathy_passed else "FAILED - needs revision",
    )

    return result


async def finalizer_node(state: GraphState) -> dict[str, Any]:
    """Finalizer node - formats the final artifact."""
    thread_id = state.get("thread_id", "unknown")

    logger.info(
        "finalizer_start",
        thread_id=thread_id,
        action="Formatting final CBT exercise artifact for human review",
    )

    start_time = time.time()
    agent = get_agent("finalizer")
    result = await agent.invoke(state)
    elapsed = time.time() - start_time

    exercise = result.get("final_exercise", {})
    logger.info(
        "finalizer_complete",
        thread_id=thread_id,
        exercise_type=exercise.get("exercise_type", "unknown"),
        exercise_title=exercise.get("title", "untitled"),
        elapsed_seconds=round(elapsed, 2),
        next_step="Human review required",
    )

    return result


async def human_review_node(state: GraphState) -> dict[str, Any]:
    """
    Human review node - interrupts for human approval.

    This node uses LangGraph's interrupt() to pause execution
    and wait for human input.
    """
    thread_id = state.get("thread_id", "unknown")
    quality_metrics = state.get("quality_metrics", {})
    safety_score = quality_metrics.get("safety", {}).get("overall_safety_score", 0)
    empathy_score = quality_metrics.get("empathy", {}).get("overall_empathy_score", 0)

    logger.info(
        "human_review_start",
        thread_id=thread_id,
        safety_score=safety_score,
        empathy_score=empathy_score,
        iteration_count=state.get("iteration_count", 0),
        action="AWAITING HUMAN REVIEW - workflow paused",
        next_step="Submit review via POST /api/v1/sessions/{id}/review",
    )

    # Prepare review data for the UI
    review_data = {
        "session_id": state.get("session_id"),
        "thread_id": thread_id,
        "current_draft": state.get("current_draft"),
        "draft_version": state.get("draft_history", {}).get("current_version", 0),
        "final_exercise": state.get("final_exercise"),
        "safety_score": safety_score,
        "empathy_score": empathy_score,
        "iteration_count": state.get("iteration_count", 0),
        "scratchpad_summary": _summarize_scratchpads(state.get("scratchpads", {})),
    }

    # This will pause execution until human provides input
    human_decision = interrupt(review_data)

    logger.info(
        "human_review_received",
        thread_id=thread_id,
        decision=human_decision.get("decision", "unknown"),
        reviewer_id=human_decision.get("reviewer_id"),
    )

    # Process human decision
    decision = human_decision.get("decision", "approve")
    from datetime import datetime

    if decision == "approve":
        return {
            "workflow_stage": "approved",
            "human_review": {
                "reviewer_id": human_decision.get("reviewer_id"),
                "decision": "approve",
                "edits": None,
                "feedback": human_decision.get("feedback"),
                "reviewed_at": datetime.utcnow().isoformat(),
                "awaiting_review": False,
            },
            "awaiting_human_input": False,
        }
    elif decision == "reject":
        return {
            "workflow_stage": "rejected",
            "human_review": {
                "reviewer_id": human_decision.get("reviewer_id"),
                "decision": "reject",
                "edits": None,
                "feedback": human_decision.get("feedback"),
                "reviewed_at": datetime.utcnow().isoformat(),
                "awaiting_review": False,
            },
            "awaiting_human_input": False,
        }
    elif decision == "edit":
        # Human made edits - update draft and re-review
        edited_content = human_decision.get("edits", state.get("current_draft"))
        draft_history = state.get("draft_history", {"current_version": 0, "versions": []})
        new_version = draft_history["current_version"] + 1
        draft_history["current_version"] = new_version
        draft_history["versions"].append({
            "version_number": new_version,
            "content": edited_content,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "human",
            "revision_notes": "Human edit",
        })

        return {
            "current_draft": edited_content,
            "draft_history": draft_history,
            "workflow_stage": "safety_review",
            "human_review": {
                "reviewer_id": human_decision.get("reviewer_id"),
                "decision": "edit",
                "edits": edited_content,
                "feedback": human_decision.get("feedback"),
                "reviewed_at": datetime.utcnow().isoformat(),
                "awaiting_review": False,
            },
            "awaiting_human_input": False,
        }

    # Default to awaiting review
    return {
        "awaiting_human_input": True,
        "human_review": {
            "awaiting_review": True,
        },
    }


def _summarize_scratchpads(scratchpads: dict) -> dict:
    """Create a summary of all agent scratchpads."""
    summary = {}
    for agent_id, scratchpad in scratchpads.items():
        notes = scratchpad.get("notes", [])
        unresolved = [n for n in notes if not n.get("resolved", False)]
        summary[agent_id] = {
            "total_notes": len(notes),
            "unresolved_notes": len(unresolved),
            "last_action": scratchpad.get("last_action"),
            "critical_flags": sum(1 for n in unresolved if n.get("severity") == "critical"),
            "major_flags": sum(1 for n in unresolved if n.get("severity") == "major"),
        }
    return summary
