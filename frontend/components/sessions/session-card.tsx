"use client";

import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { Clock, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import type { Session, SessionStatus, WorkflowStage } from "@/types/session";

interface SessionCardProps {
  session: Session;
}

const statusConfig: Record<
  SessionStatus,
  { label: string; variant: "default" | "warning" | "success" | "destructive" | "info" }
> = {
  in_progress: { label: "In Progress", variant: "info" },
  awaiting_review: { label: "Awaiting Review", variant: "warning" },
  approved: { label: "Approved", variant: "success" },
  rejected: { label: "Rejected", variant: "destructive" },
  error: { label: "Error", variant: "destructive" },
};

const stageLabels: Record<WorkflowStage, string> = {
  initializing: "Initializing",
  drafting: "Drafting",
  safety_review: "Safety Review",
  clinical_review: "Clinical Review",
  revising: "Revising",
  finalizing: "Finalizing",
  human_review: "Human Review",
  approved: "Approved",
  rejected: "Rejected",
};

export function SessionCard({ session }: SessionCardProps) {
  const config = statusConfig[session.status] || statusConfig.in_progress;
  const timeAgo = formatDistanceToNow(new Date(session.created_at), {
    addSuffix: true,
  });

  return (
    <Link href={`/sessions/${session.session_id}`}>
      <Card className="transition-shadow hover:shadow-md">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            Session {session.session_id.slice(0, 8)}...
          </CardTitle>
          <Badge variant={config.variant}>{config.label}</Badge>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3" />
              <span>{timeAgo}</span>
            </div>
            {session.workflow_stage && (
              <div className="flex items-center gap-1">
                <span>{stageLabels[session.workflow_stage]}</span>
                <ArrowRight className="h-3 w-3" />
              </div>
            )}
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            Iteration: {session.iteration_count}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
