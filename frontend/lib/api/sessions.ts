import { api } from "./client";
import type {
  Session,
  SessionState,
  SessionListResponse,
  CreateSessionRequest,
  ReviewRequest,
  ReviewResponse,
  DraftForReview,
} from "@/types/session";

export const sessionsApi = {
  /**
   * Create a new CBT exercise session
   */
  create: (request: CreateSessionRequest) =>
    api.post<Session>("/sessions", request),

  /**
   * List all sessions with pagination
   */
  list: (params?: { limit?: number; offset?: number; status?: string }) =>
    api.get<SessionListResponse>("/sessions", params),

  /**
   * Get full session state including quality metrics
   */
  get: (sessionId: string) => api.get<SessionState>(`/sessions/${sessionId}`),

  /**
   * Get draft for human review
   */
  getDraft: (sessionId: string) =>
    api.get<DraftForReview>(`/sessions/${sessionId}/draft`),

  /**
   * Submit human review decision
   */
  submitReview: (sessionId: string, review: ReviewRequest) =>
    api.post<ReviewResponse>(`/sessions/${sessionId}/review`, review),

  /**
   * Delete a session
   */
  delete: (sessionId: string) => api.delete(`/sessions/${sessionId}`),
};
