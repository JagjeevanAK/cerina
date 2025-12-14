import { api } from "./client";
import type { Exercise, ExerciseListResponse } from "@/types/session";

export const exercisesApi = {
  /**
   * List approved exercises with pagination and filters
   */
  list: (params?: {
    limit?: number;
    offset?: number;
    exercise_type?: string;
    target_condition?: string;
  }) => api.get<ExerciseListResponse>("/exercises", params),

  /**
   * Get a specific exercise by ID
   */
  get: (exerciseId: string) => api.get<Exercise>(`/exercises/${exerciseId}`),
};
