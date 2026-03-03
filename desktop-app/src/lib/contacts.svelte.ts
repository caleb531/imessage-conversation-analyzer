import { invoke } from '@tauri-apps/api/core';
import { load } from '@tauri-apps/plugin-store';
import type { Contact } from '../types';

export type ContactValues = Contact[];

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

async function initialiseSelectedContacts() {
    const store = await getStore();
    const stored = await store.get<ContactValues>('selectedContacts');
    selectedContacts.value = normalizeContacts(stored);
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
    } else {
        await store.delete('selectedContacts');
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

export async function fetchContacts(): Promise<Contact[]> {
    return invoke<Contact[]>('get_contacts');
}
