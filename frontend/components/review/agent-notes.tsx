"use client";

import { AlertTriangle, AlertCircle, Info, CheckCircle, MessageSquareText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";

interface AgentNote {
  agent_id: string;
  note_type: string;
  severity: string;
  content: string;
  resolved: boolean;
  line_reference?: number;
}

interface AgentNotesProps {
  notes: AgentNote[];
}

const severityConfig = {
  critical: {
    icon: AlertTriangle,
    color: "text-destructive",
    bgColor: "bg-destructive/5",
    borderColor: "border-destructive/30",
    badgeVariant: "destructive" as const,
  },
  major: {
    icon: AlertCircle,
    color: "text-amber-600 dark:text-amber-400",
    bgColor: "bg-amber-500/5",
    borderColor: "border-amber-500/30",
    badgeVariant: "warning" as const,
  },
  minor: {
    icon: Info,
    color: "text-sky-600 dark:text-sky-400",
    bgColor: "bg-sky-500/5",
    borderColor: "border-sky-500/30",
    badgeVariant: "info" as const,
  },
  info: {
    icon: Info,
    color: "text-muted-foreground",
    bgColor: "bg-muted/50",
    borderColor: "border-border",
    badgeVariant: "secondary" as const,
  },
};

const agentConfig: Record<string, { label: string; color: string; bgColor: string }> = {
  safety_guardian: { 
    label: "Safety Guardian", 
    color: "text-amber-600 dark:text-amber-400",
    bgColor: "bg-amber-500/10"
  },
  clinical_critic: { 
    label: "Clinical Critic", 
    color: "text-rose-600 dark:text-rose-400",
    bgColor: "bg-rose-500/10"
  },
  draftsman: { 
    label: "Draftsman", 
    color: "text-primary",
    bgColor: "bg-primary/10"
  },
  finalizer: { 
    label: "Finalizer", 
    color: "text-cyan-600 dark:text-cyan-400",
    bgColor: "bg-cyan-500/10"
  },
};

export function AgentNotes({ notes }: AgentNotesProps) {
  if (notes.length === 0) {
    return null;
  }

  // Group notes by agent
  const groupedNotes = notes.reduce<Record<string, AgentNote[]>>((acc, note) => {
    if (!acc[note.agent_id]) {
      acc[note.agent_id] = [];
    }
    acc[note.agent_id].push(note);
    return acc;
  }, {});

  // Count unresolved notes
  const unresolvedCount = notes.filter(n => !n.resolved).length;

  return (
    <Card className="border-border/50">
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <MessageSquareText className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">Agent Notes</CardTitle>
              <CardDescription>Feedback from review agents</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {unresolvedCount > 0 && (
              <Badge variant="warning" className="gap-1">
                {unresolvedCount} unresolved
              </Badge>
            )}
            <Badge variant="secondary">{notes.length} total</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {Object.entries(groupedNotes).map(([agentId, agentNotes]) => {
          const agent = agentConfig[agentId] || { 
            label: agentId, 
            color: "text-muted-foreground",
            bgColor: "bg-muted"
          };

          return (
            <div key={agentId} className="space-y-3">
              <div className="flex items-center gap-2">
                <div className={cn("h-1.5 w-1.5 rounded-full", agent.bgColor.replace("/10", ""))} />
                <h4 className={cn("text-sm font-semibold", agent.color)}>
                  {agent.label}
                </h4>
                <span className="text-xs text-muted-foreground">
                  ({agentNotes.length} {agentNotes.length === 1 ? "note" : "notes"})
                </span>
              </div>
              <div className="space-y-2 pl-3 border-l-2 border-border/50">
                {agentNotes.map((note, index) => {
                  const config =
                    severityConfig[note.severity as keyof typeof severityConfig] ||
                    severityConfig.info;
                  const Icon = config.icon;

                  return (
                    <div
                      key={index}
                      className={cn(
                        "flex items-start gap-3 rounded-xl border p-3 transition-colors",
                        config.bgColor,
                        config.borderColor,
                        note.resolved && "opacity-50"
                      )}
                    >
                      <div className={cn(
                        "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg",
                        config.bgColor.replace("/5", "/10")
                      )}>
                        <Icon className={cn("h-4 w-4", config.color)} />
                      </div>
                      <div className="flex-1 min-w-0 space-y-1.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant={config.badgeVariant} className="text-xs">
                            {note.note_type}
                          </Badge>
                          {note.resolved && (
                            <Badge variant="success" className="text-xs gap-1">
                              <CheckCircle className="h-3 w-3" />
                              Resolved
                            </Badge>
                          )}
                          {note.line_reference && (
                            <span className="text-xs text-muted-foreground font-mono">
                              Line {note.line_reference}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-foreground leading-relaxed">{note.content}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
