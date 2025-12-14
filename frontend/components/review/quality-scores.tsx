"use client";

import { Shield, Heart, RefreshCw, FileText, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface QualityScoresProps {
  safetyScore: number | null;
  empathyScore: number | null;
  iterationCount: number;
  draftVersion: number;
}

function ScoreBar({
  score,
  threshold = 0.7,
  label,
  icon: Icon,
  color,
}: {
  score: number | null;
  threshold?: number;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: {
    text: string;
    bg: string;
    fill: string;
  };
}) {
  const percentage = score !== null ? Math.round(score * 100) : 0;
  const isPassing = score !== null && score >= threshold;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg", color.bg)}>
            <Icon className={cn("h-4 w-4", color.text)} />
          </div>
          <span className="font-medium text-sm">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "text-lg font-bold tabular-nums",
              score === null
                ? "text-muted-foreground"
                : isPassing
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-destructive"
            )}
          >
            {score !== null ? `${percentage}%` : "N/A"}
          </span>
          {score !== null && (
            <div className={cn(
              "text-xs px-1.5 py-0.5 rounded font-medium",
              isPassing 
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" 
                : "bg-destructive/10 text-destructive"
            )}>
              {isPassing ? "Pass" : "Fail"}
            </div>
          )}
        </div>
      </div>
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-muted">
        {/* Threshold marker */}
        <div 
          className="absolute top-0 bottom-0 w-0.5 bg-foreground/20 z-10"
          style={{ left: `${threshold * 100}%` }}
        />
        <div
          className={cn(
            "h-full transition-all duration-700 ease-out rounded-full",
            score === null
              ? "bg-muted-foreground/20"
              : isPassing
              ? "bg-gradient-to-r from-emerald-500 to-emerald-400"
              : "bg-gradient-to-r from-destructive to-destructive/70"
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-muted/30 border border-border/50 transition-colors hover:bg-muted/50">
      <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl mb-2", color)}>
        <Icon className="h-5 w-5" />
      </div>
      <span className="text-xs text-muted-foreground font-medium">{label}</span>
      <span className="text-2xl font-bold tabular-nums text-foreground">{value}</span>
    </div>
  );
}

export function QualityScores({
  safetyScore,
  empathyScore,
  iterationCount,
  draftVersion,
}: QualityScoresProps) {
  return (
    <Card className="border-border/50 overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-base">Quality Metrics</CardTitle>
            <CardDescription>Safety and empathy evaluation scores</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="grid gap-6 lg:grid-cols-[1fr_auto]">
          {/* Score Bars */}
          <div className="space-y-5">
            <ScoreBar
              score={safetyScore}
              threshold={0.7}
              label="Safety Score"
              icon={Shield}
              color={{
                text: "text-amber-600 dark:text-amber-400",
                bg: "bg-amber-500/10",
                fill: "bg-amber-500",
              }}
            />
            <ScoreBar
              score={empathyScore}
              threshold={0.7}
              label="Empathy Score"
              icon={Heart}
              color={{
                text: "text-rose-600 dark:text-rose-400",
                bg: "bg-rose-500/10",
                fill: "bg-rose-500",
              }}
            />
          </div>

          {/* Metric Cards */}
          <div className="flex gap-3 lg:flex-col">
            <MetricCard
              icon={RefreshCw}
              label="Iterations"
              value={iterationCount}
              color="bg-violet-500/10 text-violet-600 dark:text-violet-400"
            />
            <MetricCard
              icon={FileText}
              label="Draft Version"
              value={draftVersion}
              color="bg-cyan-500/10 text-cyan-600 dark:text-cyan-400"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
