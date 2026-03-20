import type { DateFilterState } from './dateFilters';
import {
    getResultGridDateFilterState,
    setResultGridDateFilterState
} from './resultGridDateFilters.svelte';

// Standard empty-state object reused when persistence is unavailable.
const DEFAULT_DATE_FILTER_STATE: DateFilterState = {
    fromDate: '',
    toDate: ''
};

// Tracks in-flight save ordering per key so stale async failures can be ignored.
// This cache is intentionally non-reactive to avoid creating effect dependency loops.
const saveRequestVersionByKey: Record<string, number> = {};

// Loads persisted date filters for a key, or returns empty state when no key is configured.
export async function loadPersistedDateFilters(
    persistenceKey: string | undefined
): Promise<DateFilterState> {
    const normalizedKey = persistenceKey?.trim();
    if (!normalizedKey) {
        return { ...DEFAULT_DATE_FILTER_STATE };
    }

    return getResultGridDateFilterState(normalizedKey);
}

// Persists date filters for a key and suppresses stale async failures from older writes.
export async function persistDateFiltersForKey(
    persistenceKey: string | undefined,
    nextState: DateFilterState,
    callbacks: {
        onStart?: () => void;
        onError?: (_message: string) => void;
    } = {}
): Promise<void> {
    const normalizedKey = persistenceKey?.trim();
    if (!normalizedKey) {
        return;
    }

    const nextVersion = (saveRequestVersionByKey[normalizedKey] ?? 0) + 1;
    saveRequestVersionByKey[normalizedKey] = nextVersion;
    callbacks.onStart?.();

    try {
        await setResultGridDateFilterState(normalizedKey, nextState);
    } catch (error) {
        if (saveRequestVersionByKey[normalizedKey] === nextVersion) {
            const message = error instanceof Error ? error.message : String(error);
            callbacks.onError?.(message);
        }
    }
}
