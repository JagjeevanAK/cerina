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
  in_progress: "bg-blue-500",
  awaiting_review: "bg-yellow-500",
  approved: "bg-green-500",
  rejected: "bg-destructive",
  error: "bg-destructive",
} as const;

export const STAGE_COLORS = {
  initializing: "text-muted-foreground",
  drafting: "text-blue-500",
  safety_review: "text-orange-500",
  clinical_review: "text-purple-500",
  revising: "text-yellow-500",
  finalizing: "text-cyan-500",
  human_review: "text-amber-500",
  approved: "text-green-500",
  rejected: "text-destructive",
} as const;
