"use client";

import { useState, useEffect, useCallback } from "react";
import { sessionsApi } from "@/lib/api/sessions";
import { cache, CACHE_KEYS } from "@/lib/cache";
import type { SessionState, DraftForReview, ReviewRequest } from "@/types/session";
import { ApiError } from "@/lib/api/client";

const MIN_LOADING_TIME = 300;

interface UseSessionReturn {
  session: SessionState | null;
  draft: DraftForReview | null;
  isLoading: boolean;
  isSubmitting: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  fetchDraft: () => Promise<void>;
  submitReview: (review: ReviewRequest) => Promise<void>;
}

export function useSession(sessionId: string | null): UseSessionReturn {
  const [session, setSession] = useState<SessionState | null>(null);
  const [draft, setDraft] = useState<DraftForReview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    if (!sessionId) return;

    // Only show loading on initial fetch
    if (!session) {
      setIsLoading(true);
    }
    setError(null);
    const startTime = Date.now();

    try {
      const data = await sessionsApi.get(sessionId);
      
      // Ensure minimum loading time for skeleton UX on first load
      if (!session) {
        const elapsed = Date.now() - startTime;
        if (elapsed < MIN_LOADING_TIME) {
          await new Promise(resolve => setTimeout(resolve, MIN_LOADING_TIME - elapsed));
        }
      }
      
      setSession(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch session"));
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, session]);

  const fetchDraft = useCallback(async () => {
    if (!sessionId) return;

    try {
      const data = await sessionsApi.getDraft(sessionId);
      setDraft(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setDraft(null);
      } else {
        throw err;
      }
    }
  }, [sessionId]);

  const submitReview = useCallback(
    async (review: ReviewRequest) => {
      if (!sessionId) return;

      setIsSubmitting(true);
      setError(null);

      try {
        await sessionsApi.submitReview(sessionId, review);
        
        // If approved, invalidate exercises cache so it refetches with new exercise
        if (review.decision === "approve") {
          cache.invalidate(CACHE_KEYS.EXERCISES_LIST);
        }
        
        // Refetch session after review
        await refetch();
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Failed to submit review"));
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    [sessionId, refetch]
  );

  useEffect(() => {
    if (sessionId) {
      // Reset state when sessionId changes
      setSession(null);
      setDraft(null);
      setError(null);
      setIsLoading(true);
      refetch();
    }
  }, [sessionId]);

  return {
    session,
    draft,
    isLoading,
    isSubmitting,
    error,
    refetch,
    fetchDraft,
    submitReview,
  };
}
