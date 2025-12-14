"use client";

import { useState } from "react";
import { Check, X, Edit2, Loader2, FileText, MessageSquare, Eye, Pencil, Braces } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { JsonViewer } from "@/components/ui/json-viewer";
import { QualityScores } from "./quality-scores";
import { DraftViewer } from "./draft-viewer";
import { AgentNotes } from "./agent-notes";
import type { DraftForReview, ReviewRequest, ReviewDecision } from "@/types/session";
import { cn } from "@/lib/utils/cn";

interface ReviewPanelProps {
  draft: DraftForReview;
  onSubmit: (review: ReviewRequest) => Promise<void>;
  isSubmitting?: boolean;
  showNotesAndScores?: boolean;
}

export function ReviewPanel({ draft, onSubmit, isSubmitting = false, showNotesAndScores = true }: ReviewPanelProps) {
  const [mode, setMode] = useState<"view" | "edit">("view");
  const [editedDraft, setEditedDraft] = useState(draft.current_draft || "");
  const [feedback, setFeedback] = useState("");

  const handleSubmit = async (decision: ReviewDecision) => {
    await onSubmit({
      decision,
      edits: decision === "edit" ? editedDraft : undefined,
      feedback: feedback || undefined,
    });
  };

  const hasEdits = mode === "edit" && editedDraft !== draft.current_draft;

  return (
    <div className="space-y-6">
      {/* Quality Scores */}
      {showNotesAndScores && (
        <QualityScores
          safetyScore={draft.safety_score}
          empathyScore={draft.empathy_score}
          iterationCount={draft.iteration_count}
          draftVersion={draft.draft_version}
        />
      )}

      {/* Draft Content */}
      <Card className="border-border/50 overflow-hidden">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">Draft Review</CardTitle>
              <CardDescription>
                {mode === "view" ? "Review the generated content" : "Make your edits below"}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-1 rounded-lg bg-muted p-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMode("view")}
              className={cn(
                "h-8 gap-1.5 rounded-md px-3 transition-colors",
                mode === "view" && "bg-background shadow-sm"
              )}
            >
              <Eye className="h-3.5 w-3.5" />
              View
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMode("edit")}
              className={cn(
                "h-8 gap-1.5 rounded-md px-3 transition-colors",
                mode === "edit" && "bg-background shadow-sm"
              )}
            >
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {mode === "view" ? (
            <DraftViewer content={draft.current_draft || ""} />
          ) : (
            <Textarea
              value={editedDraft}
              onChange={(e) => setEditedDraft(e.target.value)}
              className="min-h-[300px] font-mono text-sm rounded-xl border-border/50 bg-muted/30 focus:bg-background transition-colors"
              placeholder="Edit the draft content..."
            />
          )}
        </CardContent>
      </Card>

      {/* Final Exercise Preview */}
      {draft.final_exercise && (
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-600 dark:text-cyan-400">
                <Braces className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">Final Exercise Structure</CardTitle>
                <CardDescription>Structured output format</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <JsonViewer data={draft.final_exercise} initialExpanded={true} />
          </CardContent>
        </Card>
      )}

      {/* Agent Notes */}
      {showNotesAndScores && draft.agent_notes.length > 0 && (
        <AgentNotes notes={draft.agent_notes} />
      )}

      {/* Feedback */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400">
              <MessageSquare className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">Feedback</CardTitle>
              <CardDescription>Optional notes for the agent to consider</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Add any feedback for the agent to consider in future iterations..."
            rows={3}
            className="rounded-xl border-border/50 bg-muted/30 focus:bg-background transition-colors"
          />
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Button
          variant="outline"
          onClick={() => handleSubmit("reject")}
          disabled={isSubmitting}
          className="gap-2 border-destructive/50 text-destructive hover:bg-destructive hover:text-destructive-foreground"
        >
          {isSubmitting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <X className="h-4 w-4" />
          )}
          Reject
        </Button>

        {hasEdits && (
          <Button
            variant="secondary"
            onClick={() => handleSubmit("edit")}
            disabled={isSubmitting}
            className="gap-2"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Edit2 className="h-4 w-4" />
            )}
            Submit Edits
          </Button>
        )}

        <Button
          onClick={() => handleSubmit("approve")}
          disabled={isSubmitting}
          className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white"
        >
          {isSubmitting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Check className="h-4 w-4" />
          )}
          Approve
        </Button>
      </div>
    </div>
  );
}
