
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

interface CacheOptions {
  /** Time in ms before data is considered stale (default: 5 min) */
  staleTime?: number;
  /** Time in ms before data is removed from cache (default: 30 min) */
  cacheTime?: number;
}

const DEFAULT_STALE_TIME = 5 * 60 * 1000; // 5 minutes
const DEFAULT_CACHE_TIME = 30 * 60 * 1000; // 30 minutes

class CacheStore {
  private cache = new Map<string, CacheEntry<unknown>>();
  private subscribers = new Map<string, Set<() => void>>();

  /**
   * Get cached data if available and not expired
   */
  get<T>(key: string, options: CacheOptions = {}): { data: T | null; isStale: boolean } {
    const entry = this.cache.get(key) as CacheEntry<T> | undefined;
    
    if (!entry) {
      return { data: null, isStale: true };
    }

    const { staleTime = DEFAULT_STALE_TIME, cacheTime = DEFAULT_CACHE_TIME } = options;
    const age = Date.now() - entry.timestamp;

    // Remove if expired
    if (age > cacheTime) {
      this.cache.delete(key);
      return { data: null, isStale: true };
    }

    // Return data with stale flag
    const isStale = age > staleTime;
    return { data: entry.data, isStale };
  }

  /**
   * Set cached data
   */
  set<T>(key: string, data: T): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
    
    // Notify subscribers
    this.notifySubscribers(key);
  }

  /**
   * Invalidate a cache entry (remove it)
   */
  invalidate(key: string): void {
    this.cache.delete(key);
    this.notifySubscribers(key);
  }

  /**
   * Invalidate all entries matching a prefix
   */
  invalidatePrefix(prefix: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.invalidate(key);
      }
    }
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.cache.clear();
    for (const key of this.subscribers.keys()) {
      this.notifySubscribers(key);
    }
  }

  /**
   * Subscribe to cache changes for a key
   */
  subscribe(key: string, callback: () => void): () => void {
    if (!this.subscribers.has(key)) {
      this.subscribers.set(key, new Set());
    }
    this.subscribers.get(key)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.subscribers.get(key)?.delete(callback);
    };
  }

  private notifySubscribers(key: string): void {
    this.subscribers.get(key)?.forEach((cb) => cb());
  }
}

// Singleton cache instance
export const cache = new CacheStore();

// Cache keys - ONLY for stable/approved data
export const CACHE_KEYS = {
  // Exercises are stable (approved by humans)
  EXERCISES_LIST: "exercises:list",
  EXERCISE: (id: string) => `exercises:${id}`,
} as const;
