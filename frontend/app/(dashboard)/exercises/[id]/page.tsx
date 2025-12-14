"use client";

import { use } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  AlertTriangle,
  ListChecks,
  RefreshCw,
  User,
  Calendar,
  Target,
  FileText,
  BookOpen,
  Shield,
  Stethoscope,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { JsonViewer } from "@/components/ui/json-viewer";
import { useExercise } from "@/hooks/use-exercises";
import { formatDistanceToNow, format } from "date-fns";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ExerciseDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const { exercise, isLoading, error, refetch } = useExercise(id);

  if (isLoading && !exercise) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
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
            <AlertTriangle className="h-5 w-5" />
            <p className="font-medium">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!exercise) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold tracking-tight">
              {exercise.title}
            </h1>
            <Badge variant="secondary">{exercise.exercise_type}</Badge>
            <Badge variant="success" className="gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Approved
            </Badge>
          </div>
          {exercise.target_condition && (
            <p className="text-sm text-muted-foreground mt-1 flex items-center gap-1.5">
              <Target className="h-3.5 w-3.5" />
              Target: <span className="text-primary">{exercise.target_condition}</span>
            </p>
          )}
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={() => refetch(true)}
          className="h-9 w-9 rounded-xl shrink-0"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {/* Meta Info */}
      <Card className="border-border/50">
        <CardContent className="pt-4">
          <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
            {exercise.approved_by && (
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <div>
                  <dt className="text-xs text-muted-foreground">Approved by</dt>
                  <dd className="font-medium">{exercise.approved_by}</dd>
                </div>
              </div>
            )}
            {exercise.approved_at && (
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <dt className="text-xs text-muted-foreground">Approved</dt>
                  <dd className="font-medium">
                    {formatDistanceToNow(new Date(exercise.approved_at), { addSuffix: true })}
                  </dd>
                </div>
              </div>
            )}
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <dt className="text-xs text-muted-foreground">Created</dt>
                <dd className="font-medium">
                  {format(new Date(exercise.created_at), "PPP")}
                </dd>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link href={`/sessions/${exercise.session_id}`} className="flex items-center gap-2 hover:text-primary transition-colors">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <div>
                  <dt className="text-xs text-muted-foreground">Session</dt>
                  <dd className="font-medium font-mono text-xs">{exercise.session_id.slice(0, 8)}...</dd>
                </div>
              </Link>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Introduction */}
      {exercise.introduction && (
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <BookOpen className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">Introduction</CardTitle>
                <CardDescription>Overview of the exercise</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
              {exercise.introduction}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Steps */}
      {exercise.steps && exercise.steps.length > 0 && (
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
                <ListChecks className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">Steps</CardTitle>
                <CardDescription>{exercise.steps.length} step{exercise.steps.length !== 1 ? "s" : ""}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {exercise.steps.map((step, index) => (
                <div
                  key={index}
                  className="flex gap-3 p-3 rounded-xl bg-muted/30 border border-border/50"
                >
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-semibold">
                    {step.step_number || index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm">{step.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      {step.anxiety_rating !== undefined && (
                        <span>Anxiety: <span className="font-medium text-foreground">{step.anxiety_rating}/10</span></span>
                      )}
                      {step.duration && (
                        <span>Duration: <span className="font-medium text-foreground">{step.duration}</span></span>
                      )}
                    </div>
                    {step.notes && (
                      <p className="text-xs text-muted-foreground mt-1 italic">{step.notes}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Safety Notes */}
      {exercise.safety_notes && exercise.safety_notes.length > 0 && (
        <Card className="border-orange-500/30 bg-orange-500/5">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500/10 text-orange-600 dark:text-orange-400">
                <Shield className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">Safety Notes</CardTitle>
                <CardDescription>{exercise.safety_notes.length} note{exercise.safety_notes.length !== 1 ? "s" : ""}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {exercise.safety_notes.map((note, index) => (
                <li key={index} className="flex items-start gap-2 text-sm">
                  <AlertTriangle className="h-4 w-4 text-orange-500 shrink-0 mt-0.5" />
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Contraindications */}
      {exercise.contraindications && exercise.contraindications.length > 0 && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
                <AlertTriangle className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">Contraindications</CardTitle>
                <CardDescription>When not to use this exercise</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {exercise.contraindications.map((item, index) => (
                <li key={index} className="flex items-start gap-2 text-sm">
                  <span className="text-destructive">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Therapist Notes */}
      {exercise.therapist_notes && (
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400">
                <Stethoscope className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">Therapist Notes</CardTitle>
                <CardDescription>Clinical guidance</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
              {exercise.therapist_notes}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Evidence Base */}
      {exercise.evidence_base && (
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-600 dark:text-cyan-400">
                <BookOpen className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">Evidence Base</CardTitle>
                <CardDescription>Research support</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
              {exercise.evidence_base}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Raw JSON */}
      <Card className="border-border/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">Raw Data</CardTitle>
              <CardDescription>Complete exercise structure</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <JsonViewer data={exercise} initialExpanded={false} />
        </CardContent>
      </Card>
    </div>
  );
}
