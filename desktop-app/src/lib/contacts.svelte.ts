import { invoke } from '@tauri-apps/api/core';
import { load } from '@tauri-apps/plugin-store';

export type ContactValue = string | null;

export const selectedContact = $state<{ value: ContactValue }>({ value: null });

let storePromise: Promise<Awaited<ReturnType<typeof load>>> | undefined;
let initPromise: Promise<void> | null = null;
let hasLoaded = false;

async function getStore() {
    if (!storePromise) {
        storePromise = load('store.json');
    }
    return storePromise;
}

async function initialiseSelectedContact() {
    const store = await getStore();
    const stored = await store.get<string>('selectedContact');
    selectedContact.value = stored ?? null;
    hasLoaded = true;
}

export async function ensureSelectedContactLoaded() {
    if (hasLoaded) {
        return;
    }
    if (!initPromise) {
        initPromise = initialiseSelectedContact().catch((error) => {
            initPromise = null;
            throw error;
        });
    }
    await initPromise;
}

export async function getSelectedContact() {
    await ensureSelectedContactLoaded();
    return selectedContact.value;
}

export async function setSelectedContact(contact: ContactValue | undefined) {
    const store = await getStore();
    if (contact) {
        await store.set('selectedContact', contact);
    } else {
        await store.delete('selectedContact');
    }
    await store.save();
    selectedContact.value = contact ?? null;
    hasLoaded = true;
}

export async function clearSelectedContact() {
    await setSelectedContact(null);
}

export async function refreshSelectedContact() {
    hasLoaded = false;
    initPromise = null;
    await ensureSelectedContactLoaded();
    return selectedContact.value;
}

export async function fetchContactNames(): Promise<string[]> {
    return invoke<string[]>('get_contact_names');
}
