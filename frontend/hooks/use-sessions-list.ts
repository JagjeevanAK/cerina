"use client";

import { useState, useEffect, useCallback } from "react";
import { sessionsApi } from "@/lib/api/sessions";
import type { Session, CreateSessionRequest, SessionListResponse } from "@/types/session";

const MIN_LOADING_TIME = 300;

interface UseSessionsListReturn {
  sessions: Session[];
  total: number;
  isLoading: boolean;
  isCreating: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  createSession: (request: CreateSessionRequest) => Promise<Session>;
}

export function useSessionsList(): UseSessionsListReturn {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const startTime = Date.now();

    try {
      const data = await sessionsApi.list({ limit: 50 });
      
      // Ensure minimum loading time for skeleton UX
      const elapsed = Date.now() - startTime;
      if (elapsed < MIN_LOADING_TIME) {
        await new Promise(resolve => setTimeout(resolve, MIN_LOADING_TIME - elapsed));
      }
      
      setSessions(data.sessions);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch sessions"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createSession = useCallback(
    async (request: CreateSessionRequest) => {
      setIsCreating(true);
      setError(null);

      try {
        const session = await sessionsApi.create(request);
        
        // Optimistically add to state
        setSessions((prev) => [session, ...prev]);
        setTotal((prev) => prev + 1);
        return session;
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Failed to create session"));
        throw err;
      } finally {
        setIsCreating(false);
      }
    },
    []
  );

  useEffect(() => {
    refetch();
  }, [refetch]);

  return {
    sessions,
    total,
    isLoading,
    isCreating,
    error,
    refetch,
    createSession,
  };
}
