"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { API_BASE_URL } from "@/lib/constants";
import type { SSEEvent, WorkflowStage } from "@/types/session";

interface UseEventSourceOptions {
  enabled?: boolean;
  onEvent?: (event: SSEEvent) => void;
  onError?: (error: Error) => void;
}

interface UseEventSourceReturn {
  events: SSEEvent[];
  currentStage: WorkflowStage | null;
  awaitingReview: boolean;
  isConnected: boolean;
  isConnecting: boolean;
  error: Error | null;
  clearEvents: () => void;
}

export function useEventSource(
  sessionId: string | null,
  options: UseEventSourceOptions = {}
): UseEventSourceReturn {
  const { enabled = true, onEvent, onError } = options;

  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [currentStage, setCurrentStage] = useState<WorkflowStage | null>(null);
  const [awaitingReview, setAwaitingReview] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setCurrentStage(null);
    setAwaitingReview(false);
    setError(null);
  }, []);

  useEffect(() => {
    if (!sessionId || !enabled) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setIsConnected(false);
      }
      return;
    }

    setIsConnecting(true);
    setError(null);

    const eventSource = new EventSource(
      `${API_BASE_URL}/sessions/${sessionId}/stream`
    );
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setIsConnecting(false);
      setError(null);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as SSEEvent;

        setEvents((prev) => [...prev, data]);
        onEvent?.(data);

        switch (data.type) {
          case "stage_changed":
            setCurrentStage(data.to_stage);
            break;
          case "human_review_needed":
            setAwaitingReview(true);
            setCurrentStage("human_review");
            break;
          case "completed":
            setCurrentStage(data.final_stage);
            // Close connection on completion
            eventSource.close();
            setIsConnected(false);
            break;
          case "error":
            setError(new Error(data.message));
            onError?.(new Error(data.message));
            break;
        }
      } catch (err) {
        console.error("Failed to parse SSE event:", err);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      setIsConnecting(false);
      const err = new Error("Connection lost. Retrying...");
      setError(err);
      onError?.(err);
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  }, [sessionId, enabled, onEvent, onError]);

  return {
    events,
    currentStage,
    awaitingReview,
    isConnected,
    isConnecting,
    error,
    clearEvents,
  };
}
