<script lang="ts">
    import { Link } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { SvelteSet } from 'svelte/reactivity';
    import { ensureSelectedContactsLoaded, selectedContacts } from '../lib/contacts.svelte';
    import { getContactBaseName, type Contact } from '../types';

    // Controls when contact labels switch to the "N others" format.
    const CONTACT_LABEL_CUTOFF_COUNT = 3;

    // Tracks whether at least one contact is selected.
    const hasContacts = $derived(selectedContacts.value.length > 0);

    // Builds the user-facing contact status message based on the selected contacts.
    const contactLabel = $derived(getContactLabel(selectedContacts.value));

    // Chooses the action text shown under the contact status.
    const actionLabel = $derived(hasContacts ? 'Change contacts' : 'Set contacts');

    onMount(() => {
        ensureSelectedContactsLoaded().catch((error) => {
            console.error('Failed to load selected contacts', error);
        });
    });

    // Formats the full status line shown in the header based on list size and naming rules.
    function getContactLabel(contacts: Contact[]): string {
        if (contacts.length === 0) {
            return 'No selected contacts';
        }

        if (contacts.length === 1) {
            return formatSingleContact(contacts[0]);
        }

        return formatMultipleContacts(contacts);
    }

    // Formats the single-contact case with the same base-label rules used elsewhere.
    function formatSingleContact(contact: Contact): string {
        return getContactBaseName(contact);
    }

    // Returns a trimmed first name when available.
    function getFirstName(contact: Contact): string {
        return contact.firstName?.trim() ?? '';
    }

    // Returns a trimmed last name when available.
    function getLastName(contact: Contact): string {
        return contact.lastName?.trim() ?? '';
    }

    // Finds first names that appear more than once so only duplicates are expanded.
    function getDuplicateFirstNames(contacts: Contact[]): SvelteSet<string> {
        const firstNameCounts: Record<string, number> = {};

        for (const contact of contacts) {
            const firstName = getFirstName(contact);
            if (!firstName) {
                continue;
            }
            const existingCount = firstNameCounts[firstName] ?? 0;
            firstNameCounts[firstName] = existingCount + 1;
        }

        const duplicateFirstNames = new SvelteSet<string>();
        for (const [firstName, count] of Object.entries(firstNameCounts)) {
            if (count > 1) {
                duplicateFirstNames.add(firstName);
            }
        }

        return duplicateFirstNames;
    }

    // Formats a contact label for multi-contact views with duplicate-first-name disambiguation.
    function formatMultiContactName(
        contact: Contact,
        duplicateFirstNames: SvelteSet<string>
    ): string {
        const firstName = getFirstName(contact);
        const lastName = getLastName(contact);

        if (!firstName) {
            return getContactBaseName(contact);
        }

        if (duplicateFirstNames.has(firstName) && lastName) {
            return `${firstName} ${lastName}`;
        }

        return firstName;
    }

    // Produces the multi-contact label with either up to cutoff names or an "N others" suffix.
    function formatMultipleContacts(contacts: Contact[]): string {
        const duplicateFirstNames = getDuplicateFirstNames(contacts);

        if (contacts.length <= CONTACT_LABEL_CUTOFF_COUNT) {
            const formattedNames = contacts.map((contact) =>
                formatMultiContactName(contact, duplicateFirstNames)
            );
            return joinWithAmpersand(formattedNames);
        }

        const visibleNameCount = Math.max(CONTACT_LABEL_CUTOFF_COUNT - 1, 1);
        const visibleNames = contacts
            .slice(0, visibleNameCount)
            .map((contact) => formatMultiContactName(contact, duplicateFirstNames));
        const remainingCount = contacts.length - visibleNameCount;

        return `${visibleNames.join(', ')}, & ${remainingCount} others`;
    }

    // Joins contact names with commas and a final ampersand for natural-language display.
    function joinWithAmpersand(values: string[]): string {
        if (values.length === 1) {
            return values[0];
        }

        if (values.length === 2) {
            return `${values[0]} & ${values[1]}`;
        }

        return `${values.slice(0, -1).join(', ')}, & ${values[values.length - 1]}`;
    }
</script>

<div class="app-header__contact-selection">
    <span class="app-header__contact-selection-names">{contactLabel}</span>
    <Link class="app-header__contact-selection-link" href="/set-contacts">
        {actionLabel}
    </Link>
</div>
