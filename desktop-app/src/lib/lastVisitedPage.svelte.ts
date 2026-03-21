import { getPersistentStore } from './store.svelte';

// Store key used to persist the most recently visited in-app route.
const LAST_VISITED_PAGE_KEY = 'lastVisitedPage';

// Default route used when no persisted value exists or data is invalid.
const DEFAULT_LAST_VISITED_PAGE = '/messages';

// Allowed in-app routes that can be persisted and restored on launch.
const ALLOWED_LAST_VISITED_PAGES = [
    '/messages',
    '/attachments',
    '/emojis',
    '/phrases',
    '/transcript',
    '/set-contacts',
    '/totals-by-day'
] as const;

// Set representation used for efficient membership checks during normalization.
const ALLOWED_LAST_VISITED_PAGE_SET = new Set<string>(ALLOWED_LAST_VISITED_PAGES);

// Canonical route type returned from last-visited page helpers.
export type LastVisitedPage = (typeof ALLOWED_LAST_VISITED_PAGES)[number];

// Normalizes unknown route-like values and strips query/hash fragments.
function normalizeRoute(value: unknown): string | undefined {
    if (typeof value !== 'string') {
        return undefined;
    }

    const trimmedValue = value.trim();
    if (!trimmedValue.startsWith('/')) {
        return undefined;
    }

    const routeWithoutHash = trimmedValue.split('#')[0] ?? '';
    const routeWithoutQuery = routeWithoutHash.split('?')[0] ?? '';
    const normalizedRoute = routeWithoutQuery.trim();

    if (!normalizedRoute || normalizedRoute === '/') {
        return undefined;
    }

    return normalizedRoute;
}

// Returns a route only when it is a supported in-app destination.
function normalizeLastVisitedPage(value: unknown): LastVisitedPage | undefined {
    const normalizedRoute = normalizeRoute(value);
    if (!normalizedRoute) {
        return undefined;
    }

    return ALLOWED_LAST_VISITED_PAGE_SET.has(normalizedRoute)
        ? (normalizedRoute as LastVisitedPage)
        : undefined;
}

// Loads the last visited page from persistence and falls back to the default route.
export async function getLastVisitedPage(): Promise<LastVisitedPage> {
    const store = await getPersistentStore();
    const persistedRoute = await store.get<string>(LAST_VISITED_PAGE_KEY);
    return normalizeLastVisitedPage(persistedRoute) ?? DEFAULT_LAST_VISITED_PAGE;
}

// Persists a route when it is a supported in-app destination.
export async function setLastVisitedPage(value: unknown): Promise<LastVisitedPage | undefined> {
    const normalizedRoute = normalizeLastVisitedPage(value);
    if (!normalizedRoute) {
        return undefined;
    }

    const store = await getPersistentStore();
    await store.set(LAST_VISITED_PAGE_KEY, normalizedRoute);
    await store.save();

    return normalizedRoute;
}
