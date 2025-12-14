// Session types matching backend schemas

export type WorkflowStage =
  | "initializing"
  | "drafting"
  | "safety_review"
  | "clinical_review"
  | "revising"
  | "finalizing"
  | "human_review"
  | "approved"
  | "rejected";

export type SessionStatus =
  | "in_progress"
  | "awaiting_review"
  | "approved"
  | "rejected"
  | "error";

export type ReviewDecision = "approve" | "reject" | "edit";

export interface QualityMetrics {
  safety_score: number | null;
  safety_passed: boolean | null;
  empathy_score: number | null;
  empathy_passed: boolean | null;
  converged: boolean;
}

export interface ScratchpadSummary {
  agent_id: string;
  total_notes: number;
  unresolved_notes: number;
  last_action: string | null;
  critical_flags: number;
  major_flags: number;
}

export interface Session {
  session_id: string;
  thread_id: string;
  status: SessionStatus;
  workflow_stage: WorkflowStage | null;
  current_agent: string | null;
  iteration_count: number;
  created_at: string;
  updated_at: string | null;
}

export interface SessionState extends Session {
  current_draft: string | null;
  draft_version: number;
  quality_metrics: QualityMetrics;
  scratchpad_summary: ScratchpadSummary[];
  awaiting_human_input: boolean;
  final_exercise: Record<string, unknown> | null;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateSessionRequest {
  user_input: string;
  exercise_type_hint?: string;
}

export interface ReviewRequest {
  decision: ReviewDecision;
  edits?: string;
  feedback?: string;
  reviewer_id?: string;
}

export interface ReviewResponse {
  session_id: string;
  thread_id: string;
  decision: string;
  workflow_stage: string;
  reviewed_at: string;
}

export interface DraftForReview {
  session_id: string;
  thread_id: string;
  current_draft: string | null;
  draft_version: number;
  final_exercise: Record<string, unknown> | null;
  safety_score: number | null;
  empathy_score: number | null;
  iteration_count: number;
  agent_notes: AgentNote[];
}

export interface AgentNote {
  agent_id: string;
  note_type: string;
  severity: string;
  content: string;
  resolved: boolean;
  line_reference?: number;
}

// SSE Event Types
export type SSEEventType =
  | "stage_changed"
  | "human_review_needed"
  | "completed"
  | "error";

export interface StageChangedEvent {
  type: "stage_changed";
  from_stage: WorkflowStage;
  to_stage: WorkflowStage;
  iteration_count: number;
}

export interface HumanReviewNeededEvent {
  type: "human_review_needed";
  draft_preview: string;
  final_exercise: Record<string, unknown>;
}

export interface CompletedEvent {
  type: "completed";
  final_stage: WorkflowStage;
  final_exercise: Record<string, unknown>;
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type SSEEvent =
  | StageChangedEvent
  | HumanReviewNeededEvent
  | CompletedEvent
  | ErrorEvent;

// Exercise types
export interface Exercise {
  id: string;
  session_id: string;
  exercise_type: string;
  title: string;
  target_condition: string | null;
  introduction: string | null;
  steps: ExerciseStep[] | null;
  safety_notes: string[] | null;
  therapist_notes: string | null;
  contraindications: string[] | null;
  evidence_base: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
}

export interface ExerciseStep {
  step_number: number;
  description: string;
  anxiety_rating?: number;
  duration?: string;
  notes?: string;
}

export interface ExerciseListResponse {
  exercises: Exercise[];
  total: number;
  limit: number;
  offset: number;
}
