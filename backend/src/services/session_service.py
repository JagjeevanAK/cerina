"""Session management service."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.cbt_models import (
    CBTSession,
    DraftVersion,
    AgentNote,
    QualityScore,
    CBTExercise,
    HumanReview,
)


class SessionService:
    """Service for managing CBT sessions in the database."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        thread_id: str,
        raw_input: str,
        user_id: Optional[UUID] = None,
    ) -> CBTSession:
        """Create a new CBT session."""
        session = CBTSession(
            thread_id=thread_id,
            raw_input=raw_input,
            user_id=user_id,
            status="in_progress",
            workflow_stage="initializing",
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: UUID) -> Optional[CBTSession]:
        """Get a session by ID."""
        result = await self.db.execute(
            select(CBTSession)
            .where(CBTSession.id == session_id)
            .options(
                selectinload(CBTSession.drafts),
                selectinload(CBTSession.notes),
                selectinload(CBTSession.scores),
                selectinload(CBTSession.exercise),
                selectinload(CBTSession.reviews),
            )
        )
        return result.scalar_one_or_none()

    async def get_session_by_thread(self, thread_id: str) -> Optional[CBTSession]:
        """Get a session by thread ID."""
        result = await self.db.execute(
            select(CBTSession)
            .where(CBTSession.thread_id == thread_id)
            .options(
                selectinload(CBTSession.drafts),
                selectinload(CBTSession.notes),
                selectinload(CBTSession.scores),
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[CBTSession], int]:
        """List sessions with optional filtering."""
        query = select(CBTSession).order_by(CBTSession.created_at.desc())

        if status:
            query = query.where(CBTSession.status == status)

        count_query = select(func.count()).select_from(CBTSession)
        if status:
            count_query = count_query.where(CBTSession.status == status)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        sessions = list(result.scalars().all())

        return sessions, total

    async def update_session(
        self,
        session_id: UUID,
        **kwargs,
    ) -> Optional[CBTSession]:
        """Update a session."""
        session = await self.get_session(session_id)
        if not session:
            return None

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update_session_from_state(
        self,
        thread_id: str,
        state: dict,
    ) -> Optional[CBTSession]:
        """Update session from LangGraph state."""
        session = await self.get_session_by_thread(thread_id)
        if not session:
            return None

        # Update basic fields
        session.workflow_stage = state.get("workflow_stage")
        session.iteration_count = state.get("iteration_count", 0)
        session.current_draft = state.get("current_draft")

        # Update user request fields
        user_request = state.get("user_request", {})
        if user_request:
            session.parsed_intent = user_request.get("intent")
            session.exercise_type = user_request.get("exercise_type")
            session.target_condition = user_request.get("target_condition")

        # Update status based on workflow stage
        stage = state.get("workflow_stage")
        if stage == "approved":
            session.status = "approved"
            session.completed_at = datetime.utcnow()
        elif stage == "rejected":
            session.status = "rejected"
            session.completed_at = datetime.utcnow()
        elif state.get("awaiting_human_input"):
            session.status = "awaiting_review"

        session.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def add_draft_version(
        self,
        session_id: UUID,
        version_number: int,
        content: str,
        created_by: str,
        revision_notes: Optional[str] = None,
    ) -> DraftVersion:
        """Add a new draft version."""
        draft = DraftVersion(
            session_id=session_id,
            version_number=version_number,
            content=content,
            created_by=created_by,
            revision_notes=revision_notes,
        )
        self.db.add(draft)
        await self.db.commit()
        await self.db.refresh(draft)
        return draft

    async def add_agent_note(
        self,
        session_id: UUID,
        agent_id: str,
        note_type: str,
        content: str,
        severity: str = "info",
        line_reference: Optional[int] = None,
    ) -> AgentNote:
        """Add an agent note."""
        note = AgentNote(
            session_id=session_id,
            agent_id=agent_id,
            note_type=note_type,
            content=content,
            severity=severity,
            line_reference=line_reference,
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def add_quality_score(
        self,
        session_id: UUID,
        iteration_number: int,
        safety_metrics: dict,
        empathy_metrics: dict,
    ) -> QualityScore:
        """Add quality scores for an iteration."""
        score = QualityScore(
            session_id=session_id,
            iteration_number=iteration_number,
            self_harm_risk=safety_metrics.get("self_harm_risk"),
            medical_advice_risk=safety_metrics.get("medical_advice_risk"),
            crisis_escalation_needed=safety_metrics.get("crisis_escalation_needed", False),
            overall_safety_score=safety_metrics.get("overall_safety_score"),
            safety_passed=safety_metrics.get("passed"),
            warmth_score=empathy_metrics.get("warmth_score"),
            clinical_accuracy=empathy_metrics.get("clinical_accuracy"),
            language_accessibility=empathy_metrics.get("language_accessibility"),
            overall_empathy_score=empathy_metrics.get("overall_empathy_score"),
            empathy_passed=empathy_metrics.get("passed"),
        )
        self.db.add(score)
        await self.db.commit()
        await self.db.refresh(score)
        return score

    async def save_exercise(
        self,
        session_id: UUID,
        exercise_data: dict,
        approved_by: Optional[str] = None,
    ) -> CBTExercise:
        """Save the final approved exercise."""
        exercise = CBTExercise(
            session_id=session_id,
            exercise_type=exercise_data.get("exercise_type", "other"),
            title=exercise_data.get("title", ""),
            target_condition=exercise_data.get("target_condition"),
            introduction=exercise_data.get("introduction"),
            steps=exercise_data.get("steps"),
            safety_notes=exercise_data.get("safety_notes"),
            therapist_notes=exercise_data.get("therapist_notes"),
            contraindications=exercise_data.get("contraindications"),
            evidence_base=exercise_data.get("evidence_base"),
            approved_by=approved_by,
            approved_at=datetime.utcnow(),
        )
        self.db.add(exercise)
        await self.db.commit()
        await self.db.refresh(exercise)
        return exercise

    async def add_review(
        self,
        session_id: UUID,
        decision: str,
        reviewer_id: Optional[str] = None,
        edits: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> HumanReview:
        """Record a human review."""
        review = HumanReview(
            session_id=session_id,
            reviewer_id=reviewer_id,
            decision=decision,
            edits=edits,
            feedback=feedback,
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a session and all related data."""
        session = await self.get_session(session_id)
        if not session:
            return False

        await self.db.delete(session)
        await self.db.commit()
        return True
