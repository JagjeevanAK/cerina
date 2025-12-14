"""Exercise API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...models.cbt_models import CBTExercise
from ...schemas.exercise import ExerciseResponse, ExerciseListResponse

router = APIRouter()


@router.get("", response_model=ExerciseListResponse)
async def list_exercises(
    exercise_type: Optional[str] = Query(None, description="Filter by exercise type"),
    target_condition: Optional[str] = Query(None, description="Filter by condition"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all approved CBT exercises."""
    query = select(CBTExercise).order_by(CBTExercise.created_at.desc())

    if exercise_type:
        query = query.where(CBTExercise.exercise_type == exercise_type)
    if target_condition:
        query = query.where(CBTExercise.target_condition.ilike(f"%{target_condition}%"))

    # Get total count
    count_query = select(func.count()).select_from(CBTExercise)
    if exercise_type:
        count_query = count_query.where(CBTExercise.exercise_type == exercise_type)
    if target_condition:
        count_query = count_query.where(
            CBTExercise.target_condition.ilike(f"%{target_condition}%")
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    exercises = list(result.scalars().all())

    return ExerciseListResponse(
        exercises=[
            ExerciseResponse(
                id=e.id,
                session_id=e.session_id,
                exercise_type=e.exercise_type,
                title=e.title,
                target_condition=e.target_condition,
                introduction=e.introduction,
                steps=e.steps,
                safety_notes=e.safety_notes,
                therapist_notes=e.therapist_notes,
                contraindications=e.contraindications,
                evidence_base=e.evidence_base,
                approved_by=e.approved_by,
                approved_at=e.approved_at,
                created_at=e.created_at,
            )
            for e in exercises
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific approved exercise."""
    result = await db.execute(
        select(CBTExercise).where(CBTExercise.id == exercise_id)
    )
    exercise = result.scalar_one_or_none()

    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    return ExerciseResponse(
        id=exercise.id,
        session_id=exercise.session_id,
        exercise_type=exercise.exercise_type,
        title=exercise.title,
        target_condition=exercise.target_condition,
        introduction=exercise.introduction,
        steps=exercise.steps,
        safety_notes=exercise.safety_notes,
        therapist_notes=exercise.therapist_notes,
        contraindications=exercise.contraindications,
        evidence_base=exercise.evidence_base,
        approved_by=exercise.approved_by,
        approved_at=exercise.approved_at,
        created_at=exercise.created_at,
    )
