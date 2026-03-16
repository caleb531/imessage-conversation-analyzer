import { load } from '@tauri-apps/plugin-store';

// Lazy-initialized promise for the app-wide persisted store instance.
let storePromise: Promise<Awaited<ReturnType<typeof load>>> | undefined;

// Returns the shared persisted store instance, creating it on first use.
export async function getPersistentStore() {
    if (!storePromise) {
        storePromise = load('store.json');
    }
    return storePromise;
}
