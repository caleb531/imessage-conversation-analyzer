import type { DateFilterState } from './dateFilters';
import { getPersistentStore } from './store.svelte';

// Root store key used to persist date filters for all ResultGrid instances.
const RESULT_GRID_DATE_FILTERS_KEY = 'resultGridDateFilters';

// Canonical empty date filter state used when persisted values are unavailable.
const DEFAULT_DATE_FILTER_STATE: DateFilterState = {
    fromDate: '',
    toDate: ''
};

// Serialized map shape that stores one date-filter object per ResultGrid key.
type ResultGridDateFilterMap = Record<string, DateFilterState>;

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
function normalizeDateFilterMap(value: unknown): ResultGridDateFilterMap {
    if (!value || typeof value !== 'object') {
        return {};
    }

    const normalizedMap: ResultGridDateFilterMap = {};

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

// Loads persisted date filters for a specific ResultGrid key.
export async function getResultGridDateFilterState(gridKey: string): Promise<DateFilterState> {
    const normalizedGridKey = gridKey.trim();
    if (!normalizedGridKey) {
        return { ...DEFAULT_DATE_FILTER_STATE };
    }

    const store = await getPersistentStore();
    const rawMap = await store.get<ResultGridDateFilterMap>(RESULT_GRID_DATE_FILTERS_KEY);
    const normalizedMap = normalizeDateFilterMap(rawMap);

    return normalizeDateFilterState(normalizedMap[normalizedGridKey]);
}

// Persists date filters for a specific ResultGrid key, deleting empty entries to keep storage compact.
export async function setResultGridDateFilterState(
    gridKey: string,
    state: DateFilterState
): Promise<DateFilterState> {
    const normalizedGridKey = gridKey.trim();
    const normalizedState = normalizeDateFilterState(state);

    if (!normalizedGridKey) {
        return normalizedState;
    }

    const store = await getPersistentStore();
    const rawMap = await store.get<ResultGridDateFilterMap>(RESULT_GRID_DATE_FILTERS_KEY);
    const normalizedMap = normalizeDateFilterMap(rawMap);

    if (isDefaultDateFilterState(normalizedState)) {
        delete normalizedMap[normalizedGridKey];
    } else {
        normalizedMap[normalizedGridKey] = normalizedState;
    }

    if (Object.keys(normalizedMap).length === 0) {
        await store.delete(RESULT_GRID_DATE_FILTERS_KEY);
    } else {
        await store.set(RESULT_GRID_DATE_FILTERS_KEY, normalizedMap);
    }

    await store.save();
    return normalizedState;
}
