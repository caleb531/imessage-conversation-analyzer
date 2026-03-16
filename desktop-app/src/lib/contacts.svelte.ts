import { invoke } from '@tauri-apps/api/core';
import type { Contact } from '../types';
import { getPersistentStore } from './store.svelte';

// Alias for selected-contact arrays used across store helpers.
export type ContactValues = Contact[];

// Reactive in-memory selected contacts mirrored from persisted store data.
export const selectedContacts = $state<{ value: ContactValues }>({ value: [] });

// In-flight initialization promise used to coalesce concurrent bootstrap calls.
let initPromise: Promise<void> | null = null;
// Guard that prevents reloading from disk on every caller request.
let hasLoaded = false;

// Normalizes persisted contacts and removes invalid or duplicate entries by contact ID.
function normalizeContacts(contacts: ContactValues | null | undefined): ContactValues {
    if (!Array.isArray(contacts)) {
        return [];
    }

    // Deduplicates persisted contacts by ID while normalizing all optional text fields.
    const uniqueContacts: Contact[] = [];
    for (const contact of contacts) {
        if (!contact || typeof contact !== 'object') {
            continue;
        }
        const normalizedId = String(contact.id ?? '').trim();
        if (!normalizedId) {
            continue;
        }
        const normalizedContact: Contact = {
            id: normalizedId,
            firstName: normalizeOptionalString(contact.firstName),
            lastName: normalizeOptionalString(contact.lastName),
            companyName: normalizeOptionalString(contact.companyName),
            phone: normalizeOptionalString(contact.phone),
            email: normalizeOptionalString(contact.email)
        };

        const existingIndex = uniqueContacts.findIndex((entry) => entry.id === normalizedId);
        if (existingIndex >= 0) {
            uniqueContacts[existingIndex] = normalizedContact;
        } else {
            uniqueContacts.push(normalizedContact);
        }
    }

    return uniqueContacts;
}

// Normalizes optional text values by trimming and dropping blank strings.
function normalizeOptionalString(value: unknown): string | undefined {
    if (typeof value !== 'string') {
        return undefined;
    }
    const trimmedValue = value.trim();
    return trimmedValue.length > 0 ? trimmedValue : undefined;
}

// Loads selected contacts from persistence into reactive in-memory state.
async function initializeSelectedContacts() {
    const store = await getPersistentStore();
    const stored = await store.get<ContactValues>('selectedContacts');
    selectedContacts.value = normalizeContacts(stored);
    hasLoaded = true;
}

// Ensures selected contacts have been loaded from persistence once per app session.
export async function ensureSelectedContactsLoaded() {
    if (hasLoaded) {
        return;
    }
    if (!initPromise) {
        initPromise = initializeSelectedContacts().catch((error) => {
            initPromise = null;
            throw error;
        });
    }
    await initPromise;
}

// Returns selected contacts after ensuring initial persistence load has completed.
export async function getSelectedContacts() {
    await ensureSelectedContactsLoaded();
    return selectedContacts.value;
}

// Persists and updates the in-memory selected contacts list.
export async function setSelectedContacts(contacts: ContactValues | null | undefined) {
    const store = await getPersistentStore();
    const normalizedContacts = normalizeContacts(contacts);
    if (normalizedContacts.length > 0) {
        await store.set('selectedContacts', normalizedContacts);
    } else {
        await store.delete('selectedContacts');
    }
    await store.save();
    selectedContacts.value = normalizedContacts;
    hasLoaded = true;
}

// Clears all selected contacts from persistence and memory.
export async function clearSelectedContacts() {
    await setSelectedContacts(null);
}

// Forces a fresh reload of selected contacts from persistence.
export async function refreshSelectedContacts() {
    hasLoaded = false;
    initPromise = null;
    await ensureSelectedContactsLoaded();
    return selectedContacts.value;
}

// Fetches all contacts from the native backend command.
export async function fetchContacts(): Promise<Contact[]> {
    try {
        return await invoke<Contact[]>('get_contacts');
    } catch (error) {
        throw new Error(`Failed to fetch contacts via get_contacts: ${String(error)}`, {
            cause: error
        });
    }
}
