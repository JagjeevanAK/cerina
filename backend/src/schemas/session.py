"""Session-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Request to create a new CBT exercise generation session."""

    user_input: str = Field(..., min_length=10, max_length=2000)
    exercise_type_hint: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_input": "Create an exposure hierarchy for agoraphobia",
                "exercise_type_hint": "exposure_hierarchy",
            }
        }
    }


class SessionResponse(BaseModel):
    """Response for session operations."""

    session_id: UUID
    thread_id: str
    status: str
    workflow_stage: Optional[str]
    current_agent: Optional[str]
    iteration_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class QualityMetricsResponse(BaseModel):
    """Quality metrics for a session."""

    safety_score: Optional[float]
    safety_passed: Optional[bool]
    empathy_score: Optional[float]
    empathy_passed: Optional[bool]
    converged: bool


class ScratchpadSummary(BaseModel):
    """Summary of agent scratchpads."""

    agent_id: str
    total_notes: int
    unresolved_notes: int
    last_action: Optional[str]
    critical_flags: int
    major_flags: int


class SessionStateResponse(BaseModel):
    """Full blackboard state for a session."""

    session_id: UUID
    thread_id: str
    status: str
    workflow_stage: Optional[str]
    current_draft: Optional[str]
    draft_version: int
    quality_metrics: QualityMetricsResponse
    scratchpad_summary: list[ScratchpadSummary]
    awaiting_human_input: bool
    final_exercise: Optional[dict[str, Any]]
    iteration_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """Response for listing sessions."""

    sessions: list[SessionResponse]
    total: int
    limit: int
    offset: int
