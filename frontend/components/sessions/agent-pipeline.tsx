"use client";

import {
  PenTool,
  Shield,
  Heart,
  CheckCircle,
  User,
  Loader2,
  Check,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { WorkflowStage } from "@/types/session";

interface AgentPipelineProps {
  currentStage: WorkflowStage | null;
  awaitingReview?: boolean;
  className?: string;
}

const stages = [
  {
    id: "initializing" as const,
    label: "Initializing",
    description: "Setting up session",
    icon: Loader2,
    activeColor: "text-stage-initializing",
    activeBg: "bg-stage-initializing/10",
    activeBorder: "border-stage-initializing",
    activeGlow: "shadow-stage-initializing/25",
  },
  {
    id: "drafting" as const,
    label: "Draftsman",
    description: "Creating initial draft",
    icon: PenTool,
    activeColor: "text-stage-drafting",
    activeBg: "bg-stage-drafting/10",
    activeBorder: "border-stage-drafting",
    activeGlow: "shadow-stage-drafting/25",
  },
  {
    id: "safety_review" as const,
    label: "Safety Guardian",
    description: "Checking safety",
    icon: Shield,
    activeColor: "text-stage-safety-review",
    activeBg: "bg-stage-safety-review/10",
    activeBorder: "border-stage-safety-review",
    activeGlow: "shadow-stage-safety-review/25",
  },
  {
    id: "clinical_review" as const,
    label: "Clinical Critic",
    description: "Evaluating empathy",
    icon: Heart,
    activeColor: "text-stage-clinical-review",
    activeBg: "bg-stage-clinical-review/10",
    activeBorder: "border-stage-clinical-review",
    activeGlow: "shadow-stage-clinical-review/25",
  },
  {
    id: "finalizing" as const,
    label: "Finalizer",
    description: "Formatting output",
    icon: CheckCircle,
    activeColor: "text-stage-finalizing",
    activeBg: "bg-stage-finalizing/10",
    activeBorder: "border-stage-finalizing",
    activeGlow: "shadow-stage-finalizing/25",
  },
  {
    id: "human_review" as const,
    label: "Human Review",
    description: "Awaiting approval",
    icon: User,
    activeColor: "text-stage-human-review",
    activeBg: "bg-stage-human-review/10",
    activeBorder: "border-stage-human-review",
    activeGlow: "shadow-stage-human-review/25",
  },
];

function getStageState(
  stageId: string,
  currentStage: WorkflowStage | null,
  awaitingReview: boolean
): "idle" | "active" | "complete" | "error" {
  // If no stage yet, show initializing as active
  if (!currentStage) {
    return stageId === "initializing" ? "active" : "idle";
  }

  const stageOrder = stages.map((s) => s.id);
  const currentIndex = stageOrder.indexOf(currentStage as typeof stages[number]["id"]);
  const stageIndex = stageOrder.indexOf(stageId as typeof stages[number]["id"]);

  // Special case for approved/rejected
  if (currentStage === "approved" || currentStage === "rejected") {
    return "complete";
  }

  // Handle revising stage - it's between clinical_review and drafting
  if (currentStage === "revising") {
    if (stageId === "drafting") return "active";
    if (stageId === "initializing") return "complete";
    return stageIndex < stageOrder.indexOf("drafting") ? "complete" : "idle";
  }

  if (stageIndex < currentIndex) return "complete";
  if (stageIndex === currentIndex) {
    if (stageId === "human_review" && awaitingReview) return "active";
    return "active";
  }
  return "idle";
}

export function AgentPipeline({
  currentStage,
  awaitingReview = false,
  className,
}: AgentPipelineProps) {
  return (
    <div className={cn("w-full", className)}>
      {/* Desktop view - horizontal */}
      <div className="hidden md:flex items-start justify-between gap-2">
        {stages.map((stage, index) => {
          const state = getStageState(stage.id, currentStage, awaitingReview);
          const Icon = stage.icon;
          const isLast = index === stages.length - 1;

          return (
            <div key={stage.id} className="flex items-center flex-1">
              {/* Stage Node */}
              <div className="flex flex-col items-center flex-1 min-w-0">
                <div
                  className={cn(
                    "relative flex h-14 w-14 items-center justify-center rounded-2xl border-2 transition-all duration-500",
                    state === "idle" && "border-border bg-muted/50 text-muted-foreground",
                    state === "active" && [
                      stage.activeBorder,
                      stage.activeBg,
                      stage.activeColor,
                      "shadow-lg",
                      stage.activeGlow,
                    ],
                    state === "complete" && "border-emerald-500 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
                    state === "error" && "border-destructive bg-destructive/10 text-destructive"
                  )}
                >
                  {state === "active" && (
                    <span className="absolute inset-0 rounded-2xl animate-ping opacity-20 bg-current" />
                  )}
                  {state === "active" ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : state === "complete" ? (
                    <Check className="h-6 w-6" />
                  ) : state === "error" ? (
                    <X className="h-6 w-6" />
                  ) : (
                    <Icon className="h-6 w-6" />
                  )}
                </div>
                <div className="mt-3 text-center">
                  <span
                    className={cn(
                      "block text-sm font-medium transition-colors duration-300",
                      state === "active" ? stage.activeColor : 
                      state === "complete" ? "text-emerald-600 dark:text-emerald-400" : 
                      "text-muted-foreground"
                    )}
                  >
                    {stage.label}
                  </span>
                  <span className="block text-xs text-muted-foreground mt-0.5">
                    {stage.description}
                  </span>
                </div>
              </div>

              {/* Connector */}
              {!isLast && (
                <div className="flex items-center h-14 px-1">
                  <div
                    className={cn(
                      "h-0.5 w-full min-w-8 transition-all duration-500 rounded-full",
                      getStageState(stages[index + 1].id, currentStage, awaitingReview) === "idle"
                        ? "bg-border"
                        : "bg-emerald-500"
                    )}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Mobile view - vertical */}
      <div className="md:hidden space-y-3">
        {stages.map((stage, index) => {
          const state = getStageState(stage.id, currentStage, awaitingReview);
          const Icon = stage.icon;
          const isLast = index === stages.length - 1;

          return (
            <div key={stage.id}>
              <div className="flex items-center gap-4">
                {/* Stage Node */}
                <div
                  className={cn(
                    "relative flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border-2 transition-all duration-500",
                    state === "idle" && "border-border bg-muted/50 text-muted-foreground",
                    state === "active" && [
                      stage.activeBorder,
                      stage.activeBg,
                      stage.activeColor,
                      "shadow-lg",
                      stage.activeGlow,
                    ],
                    state === "complete" && "border-emerald-500 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
                    state === "error" && "border-destructive bg-destructive/10 text-destructive"
                  )}
                >
                  {state === "active" && (
                    <span className="absolute inset-0 rounded-xl animate-ping opacity-20 bg-current" />
                  )}
                  {state === "active" ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : state === "complete" ? (
                    <Check className="h-5 w-5" />
                  ) : state === "error" ? (
                    <X className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>

                {/* Label */}
                <div className="flex-1 min-w-0">
                  <span
                    className={cn(
                      "block text-sm font-medium transition-colors duration-300",
                      state === "active" ? stage.activeColor : 
                      state === "complete" ? "text-emerald-600 dark:text-emerald-400" : 
                      "text-muted-foreground"
                    )}
                  >
                    {stage.label}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {stage.description}
                  </span>
                </div>
              </div>

              {/* Vertical Connector */}
              {!isLast && (
                <div className="ml-6 flex justify-center py-1">
                  <div
                    className={cn(
                      "w-0.5 h-4 transition-all duration-500 rounded-full",
                      getStageState(stages[index + 1].id, currentStage, awaitingReview) === "idle"
                        ? "bg-border"
                        : "bg-emerald-500"
                    )}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
