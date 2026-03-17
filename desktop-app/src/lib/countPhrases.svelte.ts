import { getPersistentStore } from './store.svelte';

// Store key used to persist Phrases route state across app launches.
const COUNT_PHRASES_STATE_KEY = 'phrasesState';

// Serializable state shape used by the Phrases route.
export type CountPhrasesState = {
    phrases: string[];
    useRegex: boolean;
    caseSensitive: boolean;
};

// Default state used when no persisted values are available.
const DEFAULT_COUNT_PHRASES_STATE: CountPhrasesState = {
    phrases: [],
    useRegex: false,
    caseSensitive: false
};

// Normalizes user-entered phrases by trimming, dropping blanks, and deduplicating case-insensitively.
function normalizePhrases(value: unknown): string[] {
    if (!Array.isArray(value)) {
        return [];
    }

    // Tracks seen lowercase values to keep only the first phrase variant entered.
    // eslint-disable-next-line svelte/prefer-svelte-reactivity
    const seenPhrases = new Set<string>();
    const normalizedPhrases: string[] = [];

    for (const phrase of value) {
        if (typeof phrase !== 'string') {
            continue;
        }

        const trimmedPhrase = phrase.trim();
        if (!trimmedPhrase) {
            continue;
        }

        const normalizedKey = trimmedPhrase.toLocaleLowerCase();
        if (seenPhrases.has(normalizedKey)) {
            continue;
        }

        seenPhrases.add(normalizedKey);
        normalizedPhrases.push(trimmedPhrase);
    }

    return normalizedPhrases;
}

// Converts unknown persisted data into a fully normalized Phrases state object.
function normalizeCountPhrasesState(value: unknown): CountPhrasesState {
    if (!value || typeof value !== 'object') {
        return { ...DEFAULT_COUNT_PHRASES_STATE };
    }

    const rawState = value as Partial<CountPhrasesState>;
    return {
        phrases: normalizePhrases(rawState.phrases),
        useRegex: Boolean(rawState.useRegex),
        caseSensitive: Boolean(rawState.caseSensitive)
    };
}

// Returns true when state equals defaults and can be removed from persistence.
function isDefaultCountPhrasesState(state: CountPhrasesState): boolean {
    return state.phrases.length === 0 && !state.useRegex && !state.caseSensitive;
}

// Loads and normalizes persisted Phrases route state.
export async function getCountPhrasesState(): Promise<CountPhrasesState> {
    const store = await getPersistentStore();
    const persistedState = await store.get<CountPhrasesState>(COUNT_PHRASES_STATE_KEY);
    return normalizeCountPhrasesState(persistedState);
}

// Persists a normalized Phrases route state and removes defaults to keep storage compact.
export async function setCountPhrasesState(state: CountPhrasesState): Promise<CountPhrasesState> {
    const store = await getPersistentStore();
    const normalizedState = normalizeCountPhrasesState(state);

    if (isDefaultCountPhrasesState(normalizedState)) {
        await store.delete(COUNT_PHRASES_STATE_KEY);
    } else {
        await store.set(COUNT_PHRASES_STATE_KEY, normalizedState);
    }

    await store.save();
    return normalizedState;
}
