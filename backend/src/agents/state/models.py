"""Pydantic models for the Blackboard state management."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

class AgentNote(BaseModel):
    """Individual note from an agent's review."""

    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    note_type: Literal["flag", "suggestion", "approval", "info"]
    severity: Literal["critical", "major", "minor", "info"] = "info"
    line_reference: Optional[int] = None
    content: str
    resolved: bool = False


class AgentScratchpad(BaseModel):
    """Scratchpad for a specific agent to track its observations."""

    agent_id: str
    notes: list[AgentNote] = Field(default_factory=list)
    last_action: Optional[str] = None
    iteration_contributions: int = 0

    def add_note(
        self,
        note_type: Literal["flag", "suggestion", "approval", "info"],
        content: str,
        severity: Literal["critical", "major", "minor", "info"] = "info",
        line_reference: Optional[int] = None,
    ) -> AgentNote:
        """Add a note to this scratchpad."""
        note = AgentNote(
            agent_id=self.agent_id,
            note_type=note_type,
            content=content,
            severity=severity,
            line_reference=line_reference,
        )
        self.notes.append(note)
        return note


class DraftVersion(BaseModel):
    """A single version of the CBT exercise draft."""

    version_number: int
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    revision_notes: Optional[str] = None


class DraftHistory(BaseModel):
    """Complete history of all draft versions."""

    current_version: int = 0
    versions: list[DraftVersion] = Field(default_factory=list)

    def add_version(
        self, content: str, created_by: str, notes: Optional[str] = None
    ) -> DraftVersion:
        """Add a new draft version."""
        self.current_version += 1
        version = DraftVersion(
            version_number=self.current_version,
            content=content,
            created_by=created_by,
            revision_notes=notes,
        )
        self.versions.append(version)
        return version

    @property
    def current_draft(self) -> Optional[str]:
        """Get the current draft content."""
        if self.versions:
            return self.versions[-1].content
        return None

    @property
    def previous_draft(self) -> Optional[str]:
        """Get the previous draft content for comparison."""
        if len(self.versions) >= 2:
            return self.versions[-2].content
        return None


class SafetyScore(BaseModel):
    """Safety evaluation metrics."""

    self_harm_risk: float = Field(ge=0.0, le=1.0, default=0.0)
    medical_advice_risk: float = Field(ge=0.0, le=1.0, default=0.0)
    crisis_escalation_needed: bool = False
    overall_safety_score: float = Field(ge=0.0, le=1.0, default=1.0)
    flagged_phrases: list[str] = Field(default_factory=list)
    passed: bool = True
    reviewed: bool = False


class EmpathyMetrics(BaseModel):
    """Clinical tone and empathy evaluation."""

    warmth_score: float = Field(ge=0.0, le=1.0, default=0.5)
    clinical_accuracy: float = Field(ge=0.0, le=1.0, default=0.5)
    language_accessibility: float = Field(ge=0.0, le=1.0, default=0.5)
    overall_empathy_score: float = Field(ge=0.0, le=1.0, default=0.5)
    tone_issues: list[str] = Field(default_factory=list)
    passed: bool = False
    reviewed: bool = False


class QualityMetrics(BaseModel):
    """Combined quality assessment."""

    safety: SafetyScore = Field(default_factory=SafetyScore)
    empathy: EmpathyMetrics = Field(default_factory=EmpathyMetrics)
    iteration_count: int = 0
    max_iterations: int = 5
    converged: bool = False

    def check_convergence(
        self, safety_threshold: float = 0.8, empathy_threshold: float = 0.7
    ) -> bool:
        """Check if quality metrics meet convergence criteria."""
        safety_ok = (
            self.safety.passed
            and self.safety.overall_safety_score >= safety_threshold
        )
        empathy_ok = (
            self.empathy.passed
            and self.empathy.overall_empathy_score >= empathy_threshold
        )
        self.converged = safety_ok and empathy_ok
        return self.converged

class ExposureStep(BaseModel):
    """Single step in an exposure hierarchy."""

    step_number: int
    description: str
    anxiety_rating: int = Field(ge=0, le=100)
    duration_minutes: Optional[int] = None
    safety_behaviors_to_drop: list[str] = Field(default_factory=list)
    coping_strategies: list[str] = Field(default_factory=list)


class CBTExercise(BaseModel):
    """Structured CBT exercise artifact."""

    exercise_type: Literal[
        "exposure_hierarchy",
        "thought_record",
        "behavioral_activation",
        "cognitive_restructuring",
        "relaxation_technique",
        "other",
    ]
    title: str
    target_condition: str
    introduction: str
    steps: list[ExposureStep] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    therapist_notes: Optional[str] = None
    contraindications: list[str] = Field(default_factory=list)
    evidence_base: Optional[str] = None

class UserRequest(BaseModel):
    """Parsed user input."""

    raw_input: str
    intent: Optional[str] = None
    exercise_type: Optional[str] = None
    target_condition: Optional[str] = None
    additional_context: Optional[str] = None

class HumanReview(BaseModel):
    """Human reviewer's input."""

    reviewer_id: Optional[str] = None
    decision: Optional[Literal["approve", "reject", "edit"]] = None
    edits: Optional[str] = None
    feedback: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    awaiting_review: bool = False


WorkflowStage = Literal[
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


class BlackboardState(BaseModel):
    """
    Main shared state for the CBT Clinical Review Board.
    This is the "Blackboard" that all agents read from and write to.
    """

    # Session identifiers
    session_id: UUID = Field(default_factory=uuid4)
    thread_id: str = ""

    # User request
    user_request: UserRequest

    # Draft management
    draft_history: DraftHistory = Field(default_factory=DraftHistory)

    # Agent scratchpads (keyed by agent_id)
    scratchpads: dict[str, AgentScratchpad] = Field(default_factory=dict)

    # Quality metrics
    quality_metrics: QualityMetrics = Field(default_factory=QualityMetrics)

    # Workflow state
    current_agent: Optional[str] = None
    workflow_stage: WorkflowStage = "initializing"

    # Final artifact
    final_exercise: Optional[CBTExercise] = None

    # Human review
    human_review: HumanReview = Field(default_factory=HumanReview)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

    def get_scratchpad(self, agent_id: str) -> AgentScratchpad:
        """Get or create a scratchpad for an agent."""
        if agent_id not in self.scratchpads:
            self.scratchpads[agent_id] = AgentScratchpad(agent_id=agent_id)
        return self.scratchpads[agent_id]

    def get_all_unresolved_notes(self) -> list[AgentNote]:
        """Get all unresolved notes across all scratchpads."""
        notes = []
        for scratchpad in self.scratchpads.values():
            notes.extend([n for n in scratchpad.notes if not n.resolved])
        return sorted(notes, key=lambda n: n.timestamp)

    def get_critical_issues(self) -> list[AgentNote]:
        """Get all critical severity notes."""
        return [
            n
            for n in self.get_all_unresolved_notes()
            if n.severity == "critical"
        ]

    class Config:
        arbitrary_types_allowed = True
