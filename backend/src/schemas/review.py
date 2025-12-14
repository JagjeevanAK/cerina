"""Review-related Pydantic schemas."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ReviewRequest(BaseModel):
    """Human review submission."""

    decision: Literal["approve", "reject", "edit"]
    edits: Optional[str] = None
    feedback: Optional[str] = None
    reviewer_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_edits(self):
        """Ensure edits are provided when decision is 'edit'."""
        if self.decision == "edit" and not self.edits:
            raise ValueError("Edits are required when decision is 'edit'")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "decision": "approve",
                "feedback": "Looks good!",
                "reviewer_id": "reviewer-123",
            }
        }
    }


class ReviewResponse(BaseModel):
    """Response after review submission."""

    session_id: UUID
    thread_id: str
    decision: str
    workflow_stage: str
    reviewed_at: datetime

    model_config = {"from_attributes": True}


class DraftForReviewResponse(BaseModel):
    """Draft content for human review."""

    session_id: UUID
    thread_id: str
    current_draft: Optional[str]
    draft_version: int
    final_exercise: Optional[dict]
    safety_score: Optional[float]
    empathy_score: Optional[float]
    iteration_count: int
    agent_notes: list[dict]
