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
  create: (request: CreateSessionRequest) =>
    api.post<Session>("/sessions", request),

  list: (params?: { limit?: number; offset?: number; status?: string }) =>
    api.get<SessionListResponse>("/sessions", params),

  get: (sessionId: string) => api.get<SessionState>(`/sessions/${sessionId}`),

  getDraft: (sessionId: string) =>
    api.get<DraftForReview>(`/sessions/${sessionId}/draft`),

  submitReview: (sessionId: string, review: ReviewRequest) =>
    api.post<ReviewResponse>(`/sessions/${sessionId}/review`, review),

  delete: (sessionId: string) => api.delete(`/sessions/${sessionId}`),
};
