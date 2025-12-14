"use client";

import { useEffect, use } from "react";
import { 
  RefreshCw, 
  Loader2, 
  CheckCircle, 
  XCircle,
  Clock,
  Layers,
  GitBranch,
  Activity,
  Zap,
  ChevronRight,
  MessageSquareText
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { JsonViewer } from "@/components/ui/json-viewer";
import { AgentPipeline } from "@/components/sessions/agent-pipeline";
import { ReviewPanel } from "@/components/review/review-panel";
import { AgentNotes } from "@/components/review/agent-notes";
import { QualityScores } from "@/components/review/quality-scores";
import { useSession } from "@/hooks/use-session";
import { useEventSource } from "@/hooks/use-event-source";
import { formatDistanceToNow } from "date-fns";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function SessionDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const {
    session,
    draft,
    isLoading,
    isSubmitting,
    error,
    refetch,
    fetchDraft,
    submitReview,
  } = useSession(id);

  // Determine if SSE should be enabled
  // Enable by default until we know session is completed
  const shouldEnableSSE = !session || !["approved", "rejected", "error"].includes(session.status);

  const {
    events,
    currentStage,
    awaitingReview,
    isConnected,
    isConnecting,
  } = useEventSource(id, {
    // Enable SSE for active sessions (not approved/rejected/error)
    // Also enable when session hasn't loaded yet to catch updates immediately
    enabled: shouldEnableSSE,
  });

  // Fetch draft when awaiting review
  useEffect(() => {
    if (session?.awaiting_human_input) {
      fetchDraft();
    }
  }, [session?.awaiting_human_input, fetchDraft]);

  // Refetch session when SSE indicates stage change
  useEffect(() => {
    if (currentStage) {
      refetch();
    }
  }, [currentStage, refetch]);

  if (isLoading && !session) {
    return (
      <div className="space-y-6 animate-fade-in-up">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive/50 bg-destructive/5">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-destructive">
            <XCircle className="h-5 w-5" />
            <p className="font-medium">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!session) {
    return null;
  }

  const statusConfig = {
    in_progress: { 
      label: "In Progress", 
      variant: "info" as const,
      icon: Loader2,
      iconClass: "animate-spin"
    },
    awaiting_review: { 
      label: "Awaiting Review", 
      variant: "warning" as const,
      icon: Clock,
      iconClass: ""
    },
    approved: { 
      label: "Approved", 
      variant: "success" as const,
      icon: CheckCircle,
      iconClass: ""
    },
    rejected: { 
      label: "Rejected", 
      variant: "destructive" as const,
      icon: XCircle,
      iconClass: ""
    },
    error: { 
      label: "Error", 
      variant: "destructive" as const,
      icon: XCircle,
      iconClass: ""
    },
  }[session.status];

  const StatusIcon = statusConfig.icon;

  return (
    <div className="space-y-4 stagger-children">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold tracking-tight truncate">
              Session
            </h1>
            <Badge variant={statusConfig.variant} className="gap-1.5">
              <StatusIcon className={`h-3 w-3 ${statusConfig.iconClass}`} />
              {statusConfig.label}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Created {formatDistanceToNow(new Date(session.created_at), { addSuffix: true })}
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          {isConnecting && (
            <Badge variant="outline" className="gap-1.5 text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Connecting
            </Badge>
          )}
          {isConnected && (
            <Badge variant="outline" className="gap-1.5 border-emerald-500/50 text-emerald-600 dark:text-emerald-400 bg-emerald-500/5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              Live
            </Badge>
          )}
          <Button 
            variant="outline" 
            size="icon" 
            onClick={refetch}
            className="h-9 w-9 rounded-xl hover:bg-primary/10 hover:text-primary hover:border-primary/50 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Agent Pipeline */}
      <Card className="overflow-hidden border-border/50 bg-gradient-to-br from-card to-muted/20">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">Agent Pipeline</CardTitle>
              <CardDescription>Real-time workflow progress</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-4 pb-6">
          <AgentPipeline
            currentStage={currentStage || session.workflow_stage}
            awaitingReview={awaitingReview || session.awaiting_human_input}
          />
        </CardContent>
      </Card>

      {/* Event Log */}
      {events.length > 0 && (
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400">
                <Zap className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">Event Log</CardTitle>
                <CardDescription>Recent workflow events</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-auto">
              {events.map((event, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 text-sm p-2 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <span className="font-mono text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                    {new Date().toLocaleTimeString()}
                  </span>
                  <span className="text-foreground">
                    {event.type === "stage_changed" && (
                      <span className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">{event.from_stage}</Badge>
                        <ChevronRight className="h-3 w-3 text-muted-foreground" />
                        <Badge variant="secondary" className="text-xs">{event.to_stage}</Badge>
                      </span>
                    )}
                    {event.type === "human_review_needed" && (
                      <Badge variant="warning">Human review required</Badge>
                    )}
                    {event.type === "completed" && (
                      <Badge variant="success">Completed: {event.final_stage}</Badge>
                    )}
                    {event.type === "error" && (
                      <Badge variant="destructive">Error: {event.message}</Badge>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agent Notes (shown when draft is available) */}
      {draft && draft.agent_notes.length > 0 && (
        <AgentNotes notes={draft.agent_notes} />
      )}

      {/* Quality Scores (shown when draft is available) */}
      {draft && (
        <QualityScores
          safetyScore={draft.safety_score}
          empathyScore={draft.empathy_score}
          iterationCount={draft.iteration_count}
          draftVersion={draft.draft_version}
        />
      )}

      {/* Review Panel (when awaiting review) */}
      {session.awaiting_human_input && draft && (
        <ReviewPanel
          draft={draft}
          onSubmit={submitReview}
          isSubmitting={isSubmitting}
          showNotesAndScores={false}
        />
      )}

      {/* Final Result */}
      {(session.status === "approved" || session.status === "rejected") && (
        <Card className={session.status === "approved" 
          ? "border-emerald-500/30 bg-gradient-to-br from-emerald-500/5 to-transparent" 
          : "border-destructive/30 bg-gradient-to-br from-destructive/5 to-transparent"
        }>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                session.status === "approved" 
                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" 
                  : "bg-destructive/10 text-destructive"
              }`}>
                {session.status === "approved" ? (
                  <CheckCircle className="h-5 w-5" />
                ) : (
                  <XCircle className="h-5 w-5" />
                )}
              </div>
              <div>
                <CardTitle>
                  {session.status === "approved" ? "Exercise Approved" : "Exercise Rejected"}
                </CardTitle>
                <CardDescription>
                  {session.status === "approved" 
                    ? "The exercise has been reviewed and approved for use" 
                    : "The exercise did not meet the required criteria"}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          {session.final_exercise && (
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center gap-4 text-sm">
                  <span className="font-semibold text-foreground">
                    {(session.final_exercise as { title?: string }).title || "CBT Exercise"}
                  </span>
                  <Badge variant="secondary">
                    {(session.final_exercise as { exercise_type?: string }).exercise_type || "Unknown"}
                  </Badge>
                </div>
                <JsonViewer data={session.final_exercise} initialExpanded={true} />
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Session Details */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <GitBranch className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">Session Details</CardTitle>
              <CardDescription>Technical metadata and identifiers</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1 p-3 rounded-xl bg-muted/30 border border-border/50">
              <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Session ID</dt>
              <dd className="font-mono text-xs truncate" title={session.session_id}>{session.session_id}</dd>
            </div>
            <div className="space-y-1 p-3 rounded-xl bg-muted/30 border border-border/50">
              <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Thread ID</dt>
              <dd className="font-mono text-xs truncate" title={session.thread_id}>{session.thread_id}</dd>
            </div>
            <div className="space-y-1 p-3 rounded-xl bg-muted/30 border border-border/50">
              <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Workflow Stage</dt>
              <dd className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {session.workflow_stage || "N/A"}
                </Badge>
              </dd>
            </div>
            <div className="space-y-1 p-3 rounded-xl bg-muted/30 border border-border/50">
              <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="h-3 w-3" />
                Iterations
              </dt>
              <dd className="text-lg font-semibold text-foreground">{session.iteration_count}</dd>
            </div>
            <div className="space-y-1 p-3 rounded-xl bg-muted/30 border border-border/50">
              <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Draft Version</dt>
              <dd className="text-lg font-semibold text-foreground">{session.draft_version}</dd>
            </div>
            <div className="space-y-1 p-3 rounded-xl bg-muted/30 border border-border/50">
              <dt className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Quality Converged</dt>
              <dd>
                {session.quality_metrics?.converged ? (
                  <Badge variant="success" className="text-xs">Yes</Badge>
                ) : (
                  <Badge variant="outline" className="text-xs">No</Badge>
                )}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
