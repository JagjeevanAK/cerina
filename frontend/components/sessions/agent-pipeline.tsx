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
  Brain,
  ArrowDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { WorkflowStage } from "@/types/session";

interface AgentPipelineProps {
  currentStage: WorkflowStage | null;
  awaitingReview?: boolean;
  className?: string;
}

const workerAgents = [
  {
    id: "drafting" as const,
    label: "Draftsman",
    description: "Creating initial draft",
    icon: PenTool,
    color: "amber",
  },
  {
    id: "safety_review" as const,
    label: "Safety Guardian",
    description: "Checking safety concerns",
    icon: Shield,
    color: "red",
  },
  {
    id: "clinical_review" as const,
    label: "Clinical Critic",
    description: "Evaluating tone & empathy",
    icon: Heart,
    color: "pink",
  },
  {
    id: "refinement" as const,
    label: "Finalizer",
    description: "Formatting output",
    icon: CheckCircle,
    color: "teal",
  },
];

function getAgentState(
  agentId: string,
  currentStage: WorkflowStage | null
): "idle" | "active" | "complete" {
  if (!currentStage) return "idle";

  // During initializing, draftsman is starting up
  if (currentStage === "initializing") {
    return agentId === "drafting" ? "active" : "idle";
  }

  // Map stages to worker agents
  const stageToAgent: Record<string, string> = {
    drafting: "drafting",
    revising: "drafting",
    safety_review: "safety_review",
    clinical_review: "clinical_review",
    refinement: "refinement",
    finalizing: "refinement",
  };

  if (currentStage === "approved" || currentStage === "rejected") {
    return "complete";
  }

  if (currentStage === "human_review") {
    return "complete";
  }

  if (stageToAgent[currentStage] === agentId) {
    return "active";
  }

  const visitOrder = ["drafting", "safety_review", "clinical_review", "refinement"];
  const currentAgentId = stageToAgent[currentStage] || "";
  const currentIdx = visitOrder.indexOf(currentAgentId);
  const agentIdx = visitOrder.indexOf(agentId);

  if (agentIdx !== -1 && currentIdx !== -1 && agentIdx < currentIdx) {
    return "complete";
  }

  return "idle";
}

function getActiveAgentInfo(currentStage: WorkflowStage | null): { id: string; label: string } | null {
  // During initializing, draftsman is starting
  if (currentStage === "initializing") {
    const draftsman = workerAgents.find(a => a.id === "drafting");
    return draftsman ? { id: draftsman.id, label: draftsman.label } : null;
  }

  const stageToAgent: Record<string, string> = {
    drafting: "drafting",
    revising: "drafting",
    safety_review: "safety_review",
    clinical_review: "clinical_review",
    refinement: "refinement",
    finalizing: "refinement",
  };

  const agentId = stageToAgent[currentStage || ""];
  if (!agentId) return null;

  const agent = workerAgents.find(a => a.id === agentId);
  return agent ? { id: agent.id, label: agent.label } : null;
}

function getSupervisorState(currentStage: WorkflowStage | null): "idle" | "active" | "complete" {
  if (!currentStage) return "idle";
  if (currentStage === "approved" || currentStage === "rejected") return "complete";
  if (currentStage === "human_review") return "complete";
  return "active";
}

function getHumanReviewState(
  currentStage: WorkflowStage | null,
  awaitingReview: boolean
): "idle" | "active" | "complete" {
  if (currentStage === "approved" || currentStage === "rejected") return "complete";
  if (currentStage === "human_review" || awaitingReview) return "active";
  return "idle";
}

const colorConfig: Record<string, { border: string; bg: string; text: string; glow: string; line: string }> = {
  amber: {
    border: "border-amber-500",
    bg: "bg-amber-500/10",
    text: "text-amber-600 dark:text-amber-400",
    glow: "shadow-amber-500/30",
    line: "bg-amber-500"
  },
  red: {
    border: "border-red-500",
    bg: "bg-red-500/10",
    text: "text-red-600 dark:text-red-400",
    glow: "shadow-red-500/30",
    line: "bg-red-500"
  },
  pink: {
    border: "border-pink-500",
    bg: "bg-pink-500/10",
    text: "text-pink-600 dark:text-pink-400",
    glow: "shadow-pink-500/30",
    line: "bg-pink-500"
  },
  teal: {
    border: "border-teal-500",
    bg: "bg-teal-500/10",
    text: "text-teal-600 dark:text-teal-400",
    glow: "shadow-teal-500/30",
    line: "bg-teal-500"
  },
  violet: {
    border: "border-violet-500",
    bg: "bg-violet-500/10",
    text: "text-violet-600 dark:text-violet-400",
    glow: "shadow-violet-500/30",
    line: "bg-violet-500"
  },
  blue: {
    border: "border-blue-500",
    bg: "bg-blue-500/10",
    text: "text-blue-600 dark:text-blue-400",
    glow: "shadow-blue-500/30",
    line: "bg-blue-500"
  },
  emerald: {
    border: "border-emerald-500",
    bg: "bg-emerald-500/10",
    text: "text-emerald-600 dark:text-emerald-400",
    glow: "shadow-emerald-500/30",
    line: "bg-emerald-500"
  },
};

export function AgentPipeline({
  currentStage,
  awaitingReview = false,
  className,
}: AgentPipelineProps) {
  const supervisorState = getSupervisorState(currentStage);
  const humanReviewState = getHumanReviewState(currentStage, awaitingReview);
  const activeAgent = getActiveAgentInfo(currentStage);

  return (
    <div className={cn("w-full", className)}>
      <div className="flex flex-col items-center gap-2">

        {/* === SUPERVISOR HUB (Top Center) === */}
        <div className="flex flex-col items-center mb-2">
          <div
            className={cn(
              "relative flex h-16 w-16 items-center justify-center rounded-2xl border-2 transition-all duration-500",
              supervisorState === "idle" && "border-border bg-muted/50 text-muted-foreground",
              supervisorState === "active" && [
                colorConfig.violet.border,
                colorConfig.violet.bg,
                colorConfig.violet.text,
                "shadow-lg",
                colorConfig.violet.glow,
              ],
              supervisorState === "complete" && [
                colorConfig.emerald.border,
                colorConfig.emerald.bg,
                colorConfig.emerald.text,
              ]
            )}
          >
            {supervisorState === "active" && (
              <span className="absolute inset-0 rounded-2xl animate-ping opacity-20 bg-violet-500" />
            )}
            {supervisorState === "complete" ? (
              <Check className="h-7 w-7" />
            ) : (
              <Brain className={cn("h-7 w-7", supervisorState === "active" && "animate-pulse")} />
            )}
          </div>
          <span className={cn(
            "text-sm font-semibold mt-2",
            supervisorState === "active" ? colorConfig.violet.text :
              supervisorState === "complete" ? colorConfig.emerald.text :
                "text-muted-foreground"
          )}>
            Supervisor
          </span>

          {/* Status message */}
          <span className="text-xs text-muted-foreground mt-0.5 text-center">
            {currentStage === "initializing" && "Starting workflow..."}
            {supervisorState === "active" && activeAgent && (
              <span className="flex items-center gap-1">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500" />
                </span>
                Working with {activeAgent.label}
              </span>
            )}
            {supervisorState === "complete" && "Orchestration complete"}
          </span>
        </div>

        <div className="relative flex flex-col items-center">
          {/* Horizontal connecting bar */}
          <div className="absolute top-6 left-1/2 transform -translate-x-1/2 flex items-center">
            <div className={cn(
              "h-0.5 w-[280px] rounded-full transition-all duration-300",
              supervisorState === "active" ? "bg-violet-500/50" :
                supervisorState === "complete" ? "bg-emerald-500/50" : "bg-border"
            )} />
          </div>

          {/* Vertical line from supervisor */}
          <div className={cn(
            "w-0.5 h-6 rounded-full transition-all duration-300 mb-2",
            supervisorState === "active" ? "bg-violet-500" :
              supervisorState === "complete" ? "bg-emerald-500" : "bg-border"
          )} />

          {/* Worker agents */}
          <div className="flex items-start justify-center gap-6 flex-wrap">
            {workerAgents.map((agent) => {
              const state = getAgentState(agent.id, currentStage);
              const Icon = agent.icon;
              const config = colorConfig[agent.color];
              const isActive = activeAgent?.id === agent.id;

              return (
                <div
                  key={agent.id}
                  className={cn(
                    "flex flex-col items-center transition-all duration-300",
                    isActive && "scale-110"
                  )}
                >
                  {/* Agent Node */}
                  <div
                    className={cn(
                      "relative flex h-12 w-12 items-center justify-center rounded-xl border-2 transition-all duration-500",
                      state === "idle" && "border-border bg-muted/50 text-muted-foreground",
                      state === "active" && [
                        config.border,
                        config.bg,
                        config.text,
                        "shadow-lg",
                        config.glow,
                      ],
                      state === "complete" && [
                        colorConfig.emerald.border,
                        colorConfig.emerald.bg,
                        colorConfig.emerald.text,
                      ]
                    )}
                  >
                    {state === "active" && (
                      <span className="absolute inset-0 rounded-xl animate-ping opacity-20 bg-current" />
                    )}
                    {state === "active" ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : state === "complete" ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>

                  {/* Agent Label */}
                  <span className={cn(
                    "text-xs font-medium mt-2 text-center transition-colors duration-300",
                    state === "active" ? config.text :
                      state === "complete" ? colorConfig.emerald.text :
                        "text-muted-foreground"
                  )}>
                    {agent.label}
                  </span>

                  {/* Active indicator */}
                  {isActive && (
                    <span className={cn("text-[10px] mt-0.5 font-medium", config.text)}>
                      ● Working
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* === CONNECTION TO HUMAN REVIEW === */}
        <ArrowDown className={cn(
          "h-5 w-5 transition-colors",
          humanReviewState !== "idle" ? colorConfig.blue.text : "text-muted-foreground"
        )} />

        {/* === HUMAN REVIEW NODE === */}
        <div className="flex flex-col items-center">
          <div
            className={cn(
              "relative flex h-14 w-14 items-center justify-center rounded-xl border-2 transition-all duration-500",
              humanReviewState === "idle" && "border-border bg-muted/50 text-muted-foreground",
              humanReviewState === "active" && [
                colorConfig.blue.border,
                colorConfig.blue.bg,
                colorConfig.blue.text,
                "shadow-lg",
                colorConfig.blue.glow,
              ],
              humanReviewState === "complete" && [
                colorConfig.emerald.border,
                colorConfig.emerald.bg,
                colorConfig.emerald.text,
              ]
            )}
          >
            {humanReviewState === "active" && (
              <span className="absolute inset-0 rounded-xl animate-ping opacity-20 bg-blue-500" />
            )}
            {humanReviewState === "complete" ? (
              <Check className="h-6 w-6" />
            ) : humanReviewState === "active" ? (
              <User className="h-6 w-6 animate-bounce" />
            ) : (
              <User className="h-6 w-6" />
            )}
          </div>
          <span className={cn(
            "text-sm font-medium mt-2",
            humanReviewState === "active" ? colorConfig.blue.text :
              humanReviewState === "complete" ? colorConfig.emerald.text :
                "text-muted-foreground"
          )}>
            Human Review
          </span>
          <span className="text-xs text-muted-foreground">
            {humanReviewState === "active" ? "⏳ Awaiting your approval" : "Final approval"}
          </span>
        </div>

        {/* === FINAL STATUS BADGE === */}
        {(currentStage === "approved" || currentStage === "rejected") && (
          <div className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium mt-3",
            currentStage === "approved"
              ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
              : "bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30"
          )}>
            {currentStage === "approved" ? (
              <>
                <CheckCircle className="h-4 w-4" />
                Exercise Approved ✓
              </>
            ) : (
              <>
                <X className="h-4 w-4" />
                Exercise Rejected
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
