import { invoke } from '@tauri-apps/api/core';
import { load } from '@tauri-apps/plugin-store';

export type ContactValues = string[];

export const selectedContacts = $state<{ value: ContactValues }>({ value: [] });

let storePromise: Promise<Awaited<ReturnType<typeof load>>> | undefined;
let initPromise: Promise<void> | null = null;
let hasLoaded = false;

async function getStore() {
    if (!storePromise) {
        storePromise = load('store.json');
    }
    return storePromise;
}

function normalizeContacts(contacts: ContactValues | null | undefined): ContactValues {
    if (!Array.isArray(contacts)) {
        return [];
    }
    return Array.from(
        new Set(
            contacts
                .map((contact) => contact.trim())
                .filter((contact) => contact.length > 0)
        )
    );
}

async function initialiseSelectedContacts() {
    const store = await getStore();
    const stored = await store.get<ContactValues>('selectedContacts');

    if (Array.isArray(stored)) {
        selectedContacts.value = normalizeContacts(stored);
    } else {
        const legacyStored = await store.get<string>('selectedContact');
        selectedContacts.value = legacyStored ? [legacyStored] : [];
    }
    hasLoaded = true;
}

export async function ensureSelectedContactsLoaded() {
    if (hasLoaded) {
        return;
    }
    if (!initPromise) {
        initPromise = initialiseSelectedContacts().catch((error) => {
            initPromise = null;
            throw error;
        });
    }
    await initPromise;
}

export async function getSelectedContacts() {
    await ensureSelectedContactsLoaded();
    return selectedContacts.value;
}

export async function setSelectedContacts(contacts: ContactValues | null | undefined) {
    const store = await getStore();
    const normalizedContacts = normalizeContacts(contacts);
    if (normalizedContacts.length > 0) {
        await store.set('selectedContacts', normalizedContacts);
        await store.delete('selectedContact');
    } else {
        await store.delete('selectedContacts');
        await store.delete('selectedContact');
    }
    await store.save();
    selectedContacts.value = normalizedContacts;
    hasLoaded = true;
}

export async function clearSelectedContacts() {
    await setSelectedContacts(null);
}

export async function refreshSelectedContacts() {
    hasLoaded = false;
    initPromise = null;
    await ensureSelectedContactsLoaded();
    return selectedContacts.value;
}

export async function fetchContactNames(): Promise<string[]> {
    return invoke<string[]>('get_contact_names');
}
