"""Pydantic models matching backend schemas."""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class SessionResponse(BaseModel):
    """Session creation/list response."""

    session_id: UUID
    thread_id: str
    status: str
    workflow_stage: Optional[str] = None
    current_agent: Optional[str] = None
    iteration_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class QualityMetrics(BaseModel):
    """Quality metrics from agent review."""

    safety_score: Optional[float] = None
    safety_passed: Optional[bool] = None
    empathy_score: Optional[float] = None
    empathy_passed: Optional[bool] = None
    converged: bool = False


class ScratchpadSummary(BaseModel):
    """Summary of agent scratchpad notes."""

    agent_id: str
    total_notes: int
    unresolved_notes: int
    last_action: Optional[str] = None
    critical_flags: int = 0
    major_flags: int = 0


class SessionStateResponse(BaseModel):
    """Full session state."""

    session_id: UUID
    thread_id: str
    status: str
    workflow_stage: Optional[str] = None
    current_draft: Optional[str] = None
    draft_version: int = 0
    quality_metrics: QualityMetrics = QualityMetrics()
    scratchpad_summary: list[ScratchpadSummary] = []
    awaiting_human_input: bool = False
    final_exercise: Optional[dict[str, Any]] = None
    iteration_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None


class DraftForReviewResponse(BaseModel):
    """Draft content for review."""

    session_id: UUID
    thread_id: str
    current_draft: Optional[str] = None
    draft_version: int
    final_exercise: Optional[dict[str, Any]] = None
    safety_score: Optional[float] = None
    empathy_score: Optional[float] = None
    iteration_count: int
    agent_notes: list[dict[str, Any]] = []


class ReviewRequest(BaseModel):
    """Human review submission."""

    decision: Literal["approve", "reject", "edit"]
    edits: Optional[str] = None
    feedback: Optional[str] = None
    reviewer_id: Optional[str] = "mcp-auto"


class ReviewResponse(BaseModel):
    """Review submission response."""

    session_id: UUID
    thread_id: str
    decision: str
    workflow_stage: str
    reviewed_at: datetime


class ExerciseResponse(BaseModel):
    """Approved exercise."""

    id: UUID
    session_id: UUID
    exercise_type: str
    title: str
    target_condition: Optional[str] = None
    introduction: Optional[str] = None
    steps: Optional[list[dict[str, Any]]] = None
    safety_notes: Optional[list[str]] = None
    therapist_notes: Optional[str] = None
    contraindications: Optional[list[str]] = None
    evidence_base: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime


class ExerciseListResponse(BaseModel):
    """List of exercises."""

    exercises: list[ExerciseResponse]
    total: int
    limit: int
    offset: int
