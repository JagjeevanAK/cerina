"""SQLAlchemy models for CBT Clinical Review System."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..config.database import Base


class CBTSession(Base):
    """CBT exercise generation session."""

    __tablename__ = "cbt_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    thread_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Request details
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_intent: Mapped[Optional[str]] = mapped_column(String(255))
    exercise_type: Mapped[Optional[str]] = mapped_column(String(100))
    target_condition: Mapped[Optional[str]] = mapped_column(String(255))

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="in_progress", index=True
    )
    workflow_stage: Mapped[Optional[str]] = mapped_column(String(50))
    iteration_count: Mapped[int] = mapped_column(Integer, default=0)

    # Current draft (for quick access)
    current_draft: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    drafts: Mapped[list["DraftVersion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    notes: Mapped[list["AgentNote"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    scores: Mapped[list["QualityScore"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    exercise: Mapped[Optional["CBTExercise"]] = relationship(
        back_populates="session", uselist=False
    )
    reviews: Mapped[list["HumanReview"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class DraftVersion(Base):
    """Draft version history."""

    __tablename__ = "draft_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cbt_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    revision_notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["CBTSession"] = relationship(back_populates="drafts")

    __table_args__ = (Index("idx_drafts_session", "session_id"),)


class AgentNote(Base):
    """Agent scratchpad notes."""

    __tablename__ = "agent_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cbt_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    note_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    line_reference: Mapped[Optional[int]] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["CBTSession"] = relationship(back_populates="notes")

    __table_args__ = (
        Index("idx_notes_session", "session_id"),
        Index("idx_notes_agent", "agent_id"),
    )


class QualityScore(Base):
    """Quality scores per iteration."""

    __tablename__ = "quality_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cbt_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    iteration_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Safety scores
    self_harm_risk: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    medical_advice_risk: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    crisis_escalation_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    overall_safety_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    safety_passed: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Empathy scores
    warmth_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    clinical_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    language_accessibility: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    overall_empathy_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    empathy_passed: Mapped[Optional[bool]] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["CBTSession"] = relationship(back_populates="scores")

    __table_args__ = (Index("idx_scores_session", "session_id"),)


class CBTExercise(Base):
    """Final approved CBT exercises."""

    __tablename__ = "cbt_exercises"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cbt_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    exercise_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    target_condition: Mapped[Optional[str]] = mapped_column(String(255))
    introduction: Mapped[Optional[str]] = mapped_column(Text)
    steps: Mapped[Optional[dict]] = mapped_column(JSONB)
    safety_notes: Mapped[Optional[list]] = mapped_column(JSONB)
    therapist_notes: Mapped[Optional[str]] = mapped_column(Text)
    contraindications: Mapped[Optional[list]] = mapped_column(JSONB)
    evidence_base: Mapped[Optional[str]] = mapped_column(Text)

    # Approval info
    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["CBTSession"] = relationship(back_populates="exercise")

    __table_args__ = (Index("idx_exercises_type", "exercise_type"),)


class HumanReview(Base):
    """Human review decisions."""

    __tablename__ = "human_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cbt_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    reviewer_id: Mapped[Optional[str]] = mapped_column(String(255))
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    edits: Mapped[Optional[str]] = mapped_column(Text)
    feedback: Mapped[Optional[str]] = mapped_column(Text)

    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["CBTSession"] = relationship(back_populates="reviews")

    __table_args__ = (Index("idx_reviews_session", "session_id"),)


class AuditLog(Base):
    """Audit log for compliance."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cbt_sessions.id", ondelete="SET NULL"),
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_audit_session", "session_id"),
        Index("idx_audit_created", "created_at"),
    )
