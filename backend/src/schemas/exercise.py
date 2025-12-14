"""Exercise-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ExerciseStepResponse(BaseModel):
    """Single step in an exercise."""

    step_number: int
    description: str
    anxiety_rating: int
    duration_minutes: Optional[int]
    safety_behaviors_to_drop: list[str]
    coping_strategies: list[str]


class ExerciseResponse(BaseModel):
    """Response for a CBT exercise."""

    id: UUID
    session_id: UUID
    exercise_type: str
    title: str
    target_condition: Optional[str]
    introduction: Optional[str]
    steps: Optional[list[dict[str, Any]]]
    safety_notes: Optional[list[str]]
    therapist_notes: Optional[str]
    contraindications: Optional[list[str]]
    evidence_base: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class ExerciseListResponse(BaseModel):
    """Response for listing exercises."""

    exercises: list[ExerciseResponse]
    total: int
    limit: int
    offset: int
