"use client";

import { Plus, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SessionCard } from "@/components/sessions/session-card";
import { CreateSessionDialog } from "@/components/sessions/create-session-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useSessionsList } from "@/hooks/use-sessions-list";

export default function SessionsPage() {
  const { sessions, total, isLoading, isCreating, error, refetch, createSession } =
    useSessionsList();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Sessions</h1>
          <p className="text-muted-foreground">
            {total} session{total !== 1 ? "s" : ""} total
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={refetch}>
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <CreateSessionDialog
            trigger={
              <Button disabled={isCreating}>
                {isCreating ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="mr-2 h-4 w-4" />
                )}
                New Session
              </Button>
            }
            onSubmit={createSession}
          />
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-destructive">
          {error.message}
        </div>
      )}

      {/* Loading State */}
      {isLoading && sessions.length === 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && sessions.length === 0 && !error && (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <h3 className="text-lg font-medium">No sessions yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Create your first CBT exercise session to get started.
          </p>
          <CreateSessionDialog
            trigger={
              <Button className="mt-4">
                <Plus className="mr-2 h-4 w-4" />
                Create Session
              </Button>
            }
            onSubmit={createSession}
          />
        </div>
      )}

      {/* Sessions Grid */}
      {sessions.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sessions.map((session) => (
            <SessionCard key={session.session_id} session={session} />
          ))}
        </div>
      )}
    </div>
  );
}
