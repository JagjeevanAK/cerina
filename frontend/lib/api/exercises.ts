import { api } from "./client";
import type { Exercise, ExerciseListResponse } from "@/types/session";

export const exercisesApi = {
  list: (params?: {
    limit?: number;
    offset?: number;
    exercise_type?: string;
    target_condition?: string;
  }) => api.get<ExerciseListResponse>("/exercises", params),

  get: (exerciseId: string) => api.get<Exercise>(`/exercises/${exerciseId}`),
};
