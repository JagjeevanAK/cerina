export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const WORKFLOW_STAGES = [
  { id: "drafting", label: "Draftsman", description: "Creating exercise draft" },
  { id: "safety_review", label: "Safety Guardian", description: "Checking safety concerns" },
  { id: "clinical_review", label: "Clinical Critic", description: "Evaluating tone and empathy" },
  { id: "finalizing", label: "Finalizer", description: "Formatting final artifact" },
  { id: "human_review", label: "Human Review", description: "Awaiting approval" },
] as const;

export const STATUS_COLORS = {
  in_progress: "bg-status-in-progress",
  awaiting_review: "bg-status-awaiting-review",
  approved: "bg-status-approved",
  rejected: "bg-status-rejected",
  error: "bg-status-error",
} as const;

export const STAGE_COLORS = {
  initializing: "text-stage-initializing",
  drafting: "text-stage-drafting",
  safety_review: "text-stage-safety-review",
  clinical_review: "text-stage-clinical-review",
  revising: "text-stage-revising",
  finalizing: "text-stage-finalizing",
  human_review: "text-stage-human-review",
  approved: "text-stage-approved",
  rejected: "text-stage-rejected",
} as const;
