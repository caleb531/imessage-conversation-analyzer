import { load } from '@tauri-apps/plugin-store';
import { get, writable } from 'svelte/store';

export type ContactValue = string | null;

const selectedContact = writable<ContactValue | undefined>(undefined);

let storePromise: Promise<Awaited<ReturnType<typeof load>>> | null = null;
let initPromise: Promise<void> | null = null;

async function getStore() {
    if (!storePromise) {
        storePromise = load('store.json');
    }
    return storePromise;
}

async function initialiseSelectedContact() {
    const store = await getStore();
    const stored = await store.get<string>('selectedContact');
    selectedContact.set(stored ?? null);
}

export function ensureSelectedContactLoaded() {
    if (!initPromise) {
        initPromise = initialiseSelectedContact().catch((error) => {
            initPromise = null;
            throw error;
        });
    }
    return initPromise;
}

export async function getSelectedContact() {
    await ensureSelectedContactLoaded();
    const current = get(selectedContact);
    return current ?? null;
}

export async function setSelectedContact(contact: ContactValue) {
    const store = await getStore();
    if (contact) {
        await store.set('selectedContact', contact);
    } else {
        await store.delete('selectedContact');
    }
    await store.save();
    selectedContact.set(contact);
}

export async function clearSelectedContact() {
    await setSelectedContact(null);
}

export async function refreshSelectedContact() {
    initPromise = null;
    await ensureSelectedContactLoaded();
    return getSelectedContact();
}

export { selectedContact };
