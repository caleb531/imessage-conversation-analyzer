import { getPersistentStore } from './store.svelte';

// Canonical date filter values used across CLI argument building and persistence.
export interface DateFilterState {
    fromDate: string;
    toDate: string;
}

// Root key used to persist date filters for all analyzer contexts.
const DATE_FILTERS_STORE_KEY = 'resultGridDateFilters';

// Two-digit padding keeps month/day values in ISO-compatible shape.
const TIME_UNIT_PAD_LENGTH = 2;

// Canonical empty state reused when filters are unavailable or invalid.
const DEFAULT_DATE_FILTER_STATE: DateFilterState = {
    fromDate: '',
    toDate: ''
};

// Serialized map shape that stores one date-filter object per persistence key.
type PersistedDateFilterMap = Record<string, DateFilterState>;

// Tracks in-flight save ordering per key so stale async failures can be ignored.
// This cache is intentionally non-reactive to avoid creating effect dependency loops.
const saveRequestVersionByKey: Record<string, number> = {};

// Normalizes numeric date units to two characters (e.g., 3 -> 03).
function padTimeUnit(value: number): string {
    return String(value).padStart(TIME_UNIT_PAD_LENGTH, '0');
}

// Accepts either YYYY-MM-DD or M/D/YYYY and returns normalized YYYY-MM-DD.
export function normalizeDateInput(value: string): string | null {
    const trimmed = value.trim();
    if (!trimmed) return null;

    const isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trimmed);
    if (isoMatch) return trimmed;

    const slashMatch = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(trimmed);
    if (slashMatch) {
        const month = padTimeUnit(Number(slashMatch[1]));
        const day = padTimeUnit(Number(slashMatch[2]));
        return `${slashMatch[3]}-${month}-${day}`;
    }

    return null;
}

// Converts filter state into optional ICA CLI flags.
export function buildDateFilterArgs(filters: DateFilterState): string[] {
    const args: string[] = [];
    const fromValue = normalizeDateInput(filters.fromDate);
    const toValue = normalizeDateInput(filters.toDate);

    if (fromValue) {
        args.push('--from-date', fromValue);
    }
    if (toValue) {
        args.push('--to-date', toValue);
    }

    return args;
}

// Normalizes an individual date input by coercing to string and trimming whitespace.
function normalizeDateField(value: unknown): string {
    if (typeof value !== 'string') {
        return '';
    }
    return value.trim();
}

// Normalizes unknown values into the canonical DateFilterState shape.
function normalizeDateFilterState(value: unknown): DateFilterState {
    if (!value || typeof value !== 'object') {
        return { ...DEFAULT_DATE_FILTER_STATE };
    }

    const rawFilters = value as Partial<DateFilterState>;
    return {
        fromDate: normalizeDateField(rawFilters.fromDate),
        toDate: normalizeDateField(rawFilters.toDate)
    };
}

// Normalizes persisted map values and keeps only non-empty string keys.
function normalizeDateFilterMap(value: unknown): PersistedDateFilterMap {
    if (!value || typeof value !== 'object') {
        return {};
    }

    const normalizedMap: PersistedDateFilterMap = {};

    for (const [rawKey, rawState] of Object.entries(value)) {
        const key = rawKey.trim();
        if (!key) {
            continue;
        }
        normalizedMap[key] = normalizeDateFilterState(rawState);
    }

    return normalizedMap;
}

// Returns true when a date filter state is equivalent to the default empty state.
function isDefaultDateFilterState(state: DateFilterState): boolean {
    return !state.fromDate && !state.toDate;
}

// Loads date filters for a specific persistence key from local store.
async function getDateFilterStateForKey(persistenceKey: string): Promise<DateFilterState> {
    const normalizedKey = persistenceKey.trim();
    if (!normalizedKey) {
        return { ...DEFAULT_DATE_FILTER_STATE };
    }

    const store = await getPersistentStore();
    const rawMap = await store.get<PersistedDateFilterMap>(DATE_FILTERS_STORE_KEY);
    const normalizedMap = normalizeDateFilterMap(rawMap);

    return normalizeDateFilterState(normalizedMap[normalizedKey]);
}

// Saves date filters for a specific persistence key and removes empty entries.
async function setDateFilterStateForKey(
    persistenceKey: string,
    state: DateFilterState
): Promise<DateFilterState> {
    const normalizedKey = persistenceKey.trim();
    const normalizedState = normalizeDateFilterState(state);

    if (!normalizedKey) {
        return normalizedState;
    }

    const store = await getPersistentStore();
    const rawMap = await store.get<PersistedDateFilterMap>(DATE_FILTERS_STORE_KEY);
    const normalizedMap = normalizeDateFilterMap(rawMap);

    if (isDefaultDateFilterState(normalizedState)) {
        delete normalizedMap[normalizedKey];
    } else {
        normalizedMap[normalizedKey] = normalizedState;
    }

    if (Object.keys(normalizedMap).length === 0) {
        await store.delete(DATE_FILTERS_STORE_KEY);
    } else {
        await store.set(DATE_FILTERS_STORE_KEY, normalizedMap);
    }

    await store.save();
    return normalizedState;
}

// Loads persisted date filters for a key, or returns empty state when no key is configured.
export async function loadPersistedDateFilters(
    persistenceKey: string | undefined
): Promise<DateFilterState> {
    const normalizedKey = persistenceKey?.trim();
    if (!normalizedKey) {
        return { ...DEFAULT_DATE_FILTER_STATE };
    }

    return getDateFilterStateForKey(normalizedKey);
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
        await setDateFilterStateForKey(normalizedKey, nextState);
    } catch (error) {
        if (saveRequestVersionByKey[normalizedKey] === nextVersion) {
            const message = error instanceof Error ? error.message : String(error);
            callbacks.onError?.(message);
        }
    }
}