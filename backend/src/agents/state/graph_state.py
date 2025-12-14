"""LangGraph-compatible TypedDict state with annotations."""

from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import add_messages

from src.agents.state.reducers import merge_scratchpads


class GraphState(TypedDict, total=False):
    """
    LangGraph-compatible state using TypedDict with annotations.

    This state is used by the LangGraph StateGraph and supports
    reducers for safe concurrent updates.
    """

    # Core identifiers
    session_id: str
    thread_id: str

    # User input
    user_request: dict  # Serialized UserRequest

    # Draft tracking
    draft_history: dict  # Serialized DraftHistory
    current_draft: str

    # Agent scratchpads - using custom reducer for merge
    scratchpads: Annotated[dict, merge_scratchpads]

    # Quality metrics
    quality_metrics: dict  # Serialized QualityMetrics

    # Workflow control
    current_agent: str
    workflow_stage: Literal[
        "initializing",
        "drafting",
        "safety_review",
        "clinical_review",
        "revising",
        "finalizing",
        "human_review",
        "approved",
        "rejected",
    ]
    iteration_count: int

    # Final output
    final_exercise: dict | None

    # Human review
    human_review: dict
    awaiting_human_input: bool

    # Messages with built-in add reducer for conversation history
    messages: Annotated[list, add_messages]

    # Metadata
    created_at: str
    updated_at: str
    error_message: str | None


def create_initial_state(
    user_input: str,
    session_id: str | None = None,
    thread_id: str | None = None,
) -> GraphState:
    """
    Create an initial graph state from user input.

    Args:
        user_input: The raw user input string
        session_id: Optional session ID (generated if not provided)
        thread_id: Optional thread ID (generated if not provided)

    Returns:
        Initial GraphState ready for graph execution
    """
    from datetime import datetime
    from uuid import uuid4

    now = datetime.utcnow().isoformat()
    session_id = session_id or str(uuid4())
    thread_id = thread_id or str(uuid4())

    return GraphState(
        session_id=session_id,
        thread_id=thread_id,
        user_request={
            "raw_input": user_input,
            "intent": None,
            "exercise_type": None,
            "target_condition": None,
            "additional_context": None,
        },
        draft_history={
            "current_version": 0,
            "versions": [],
        },
        current_draft="",
        scratchpads={},
        quality_metrics={
            "safety": {
                "self_harm_risk": 0.0,
                "medical_advice_risk": 0.0,
                "crisis_escalation_needed": False,
                "overall_safety_score": 1.0,
                "flagged_phrases": [],
                "passed": True,
                "reviewed": False,
            },
            "empathy": {
                "warmth_score": 0.5,
                "clinical_accuracy": 0.5,
                "language_accessibility": 0.5,
                "overall_empathy_score": 0.5,
                "tone_issues": [],
                "passed": False,
                "reviewed": False,
            },
            "iteration_count": 0,
            "max_iterations": 5,
            "converged": False,
        },
        current_agent="supervisor",
        workflow_stage="initializing",
        iteration_count=0,
        final_exercise=None,
        human_review={
            "reviewer_id": None,
            "decision": None,
            "edits": None,
            "feedback": None,
            "reviewed_at": None,
            "awaiting_review": False,
        },
        awaiting_human_input=False,
        messages=[],
        created_at=now,
        updated_at=now,
        error_message=None,
    )
