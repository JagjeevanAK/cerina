"use client";

import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { Clock, ArrowRight, CheckCircle2, ListChecks, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Exercise } from "@/types/session";

interface ExerciseCardProps {
  exercise: Exercise;
}

export function ExerciseCard({ exercise }: ExerciseCardProps) {
  const timeAgo = formatDistanceToNow(new Date(exercise.created_at), {
    addSuffix: true,
  });

  return (
    <Link href={`/exercises/${exercise.id}`}>
      <Card className="transition-all hover:shadow-md hover:border-primary/50">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
          <div className="flex-1 min-w-0 pr-2">
            <CardTitle className="text-sm font-medium truncate">
              {exercise.title}
            </CardTitle>
            {exercise.target_condition && (
              <p className="text-xs text-muted-foreground mt-0.5 truncate">
                {exercise.target_condition}
              </p>
            )}
          </div>
          <Badge variant="success" className="gap-1 shrink-0">
            <CheckCircle2 className="h-3 w-3" />
            Approved
          </Badge>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3" />
              <span>{timeAgo}</span>
            </div>
            <Badge variant="secondary" className="text-xs">
              {exercise.exercise_type}
            </Badge>
          </div>
          
          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
            {exercise.steps && exercise.steps.length > 0 && (
              <div className="flex items-center gap-1">
                <ListChecks className="h-3 w-3 text-amber-500" />
                <span>{exercise.steps.length} steps</span>
              </div>
            )}
            {exercise.safety_notes && exercise.safety_notes.length > 0 && (
              <div className="flex items-center gap-1">
                <AlertTriangle className="h-3 w-3 text-orange-500" />
                <span>{exercise.safety_notes.length} safety notes</span>
              </div>
            )}
            {exercise.approved_by && (
              <div className="flex items-center gap-1 ml-auto">
                <span>by {exercise.approved_by}</span>
                <ArrowRight className="h-3 w-3" />
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
