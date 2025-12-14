"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { exercisesApi } from "@/lib/api/exercises";
import { cache, CACHE_KEYS } from "@/lib/cache";
import type { Exercise, ExerciseListResponse } from "@/types/session";

const MIN_LOADING_TIME = 300;

interface UseExercisesListReturn {
  exercises: Exercise[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  refetch: (force?: boolean) => Promise<void>;
}

/**
 * Hook for fetching exercises list with caching.
 * Exercises are stable (approved) data, so caching is appropriate.
 */
export function useExercisesList(): UseExercisesListReturn {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const initialFetchDone = useRef(false);

  const refetch = useCallback(async (force = false) => {
    const cached = cache.get<ExerciseListResponse>(CACHE_KEYS.EXERCISES_LIST);
    
    // Use cached data if fresh and not forcing
    if (cached.data && !cached.isStale && !force && initialFetchDone.current) {
      setExercises(cached.data.exercises);
      setTotal(cached.data.total);
      setIsLoading(false);
      return;
    }

    // Show stale data immediately while fetching
    if (cached.data) {
      setExercises(cached.data.exercises);
      setTotal(cached.data.total);
    }

    // Only show loading if no data
    if (!cached.data) {
      setIsLoading(true);
    }

    setError(null);
    const startTime = Date.now();

    try {
      const data = await exercisesApi.list({ limit: 50 });
      
      // Ensure minimum loading time for skeleton UX on first load
      if (!cached.data && !initialFetchDone.current) {
        const elapsed = Date.now() - startTime;
        if (elapsed < MIN_LOADING_TIME) {
          await new Promise(resolve => setTimeout(resolve, MIN_LOADING_TIME - elapsed));
        }
      }
      
      // Cache the list
      cache.set(CACHE_KEYS.EXERCISES_LIST, data);
      
      // Cache individual exercises
      data.exercises.forEach(exercise => {
        cache.set(CACHE_KEYS.EXERCISE(exercise.id), exercise);
      });
      
      setExercises(data.exercises);
      setTotal(data.total);
      initialFetchDone.current = true;
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch exercises"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
    
    // Subscribe to cache invalidation (e.g., when a new exercise is approved)
    const unsubscribe = cache.subscribe(CACHE_KEYS.EXERCISES_LIST, () => {
      const cached = cache.get<ExerciseListResponse>(CACHE_KEYS.EXERCISES_LIST);
      if (cached.data) {
        setExercises(cached.data.exercises);
        setTotal(cached.data.total);
      } else if (cached.isStale) {
        // Cache was invalidated, refetch
        refetch(true);
      }
    });
    
    return unsubscribe;
  }, [refetch]);

  return {
    exercises,
    total,
    isLoading,
    error,
    refetch,
  };
}

interface UseExerciseReturn {
  exercise: Exercise | null;
  isLoading: boolean;
  error: Error | null;
  refetch: (force?: boolean) => Promise<void>;
}

/**
 * Hook for fetching a single exercise with caching.
 * Exercises are stable (approved) data, so caching is appropriate.
 */
export function useExercise(exerciseId: string | null): UseExerciseReturn {
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async (force = false) => {
    if (!exerciseId) return;

    const cacheKey = CACHE_KEYS.EXERCISE(exerciseId);
    const cached = cache.get<Exercise>(cacheKey);

    // Use cached data if fresh and not forcing
    if (cached.data && !cached.isStale && !force) {
      setExercise(cached.data);
      setIsLoading(false);
      return;
    }

    // Show stale data while fetching
    if (cached.data) {
      setExercise(cached.data);
    }

    if (!cached.data) {
      setIsLoading(true);
    }

    setError(null);
    const startTime = Date.now();

    try {
      const data = await exercisesApi.get(exerciseId);
      
      if (!cached.data) {
        const elapsed = Date.now() - startTime;
        if (elapsed < MIN_LOADING_TIME) {
          await new Promise(resolve => setTimeout(resolve, MIN_LOADING_TIME - elapsed));
        }
      }
      
      cache.set(cacheKey, data);
      setExercise(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch exercise"));
    } finally {
      setIsLoading(false);
    }
  }, [exerciseId]);

  useEffect(() => {
    if (exerciseId) {
      setExercise(null);
      setError(null);
      refetch();
    }
  }, [exerciseId, refetch]);

  return {
    exercise,
    isLoading,
    error,
    refetch,
  };
}
