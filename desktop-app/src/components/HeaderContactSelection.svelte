<script lang="ts">
    import { Link } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { ensureSelectedContactsLoaded, selectedContacts } from '../lib/contacts.svelte';

    type ParsedContact = {
        originalName: string;
        firstName: string;
        lastName: string;
    };

    // Controls when contact labels switch to the "N others" format.
    const CONTACT_LABEL_CUTOFF_COUNT = 3;

    // Tracks whether at least one contact is selected.
    const hasContacts = $derived(selectedContacts.value.length > 0);

    // Normalizes selected contact strings into first/last-name parts for display logic.
    const parsedContacts = $derived(
        selectedContacts.value.map((contact) => parseContactName(contact))
    );

    // Tracks first names that appear more than once so only those entries can be disambiguated.
    const duplicateFirstNames = $derived(getDuplicateFirstNames(parsedContacts));

    // Builds the user-facing contact status message based on the selected contacts.
    const contactLabel = $derived(getContactLabel(parsedContacts, duplicateFirstNames));

    // Chooses the action text shown under the contact status.
    const actionLabel = $derived(hasContacts ? 'Change contacts' : 'Set contacts');

    onMount(() => {
        ensureSelectedContactsLoaded().catch((error) => {
            console.error('Failed to load selected contacts', error);
        });
    });

    // Parses an individual contact name into first-name and last-name display parts.
    function parseContactName(contact: string): ParsedContact {
        const trimmedContact = contact.trim();
        const nameParts = trimmedContact.split(/\s+/).filter((part) => part.length > 0);
        const firstName = nameParts[0] ?? trimmedContact;
        const lastName = nameParts.length > 1 ? nameParts[nameParts.length - 1] : '';

        return {
            originalName: trimmedContact,
            firstName,
            lastName
        };
    }

    // Finds first names that are duplicated in the selected contact list.
    function getDuplicateFirstNames(contacts: ParsedContact[]): Set<string> {
        const firstNameCounts = new Map<string, number>();

        for (const contact of contacts) {
            const existingCount = firstNameCounts.get(contact.firstName) ?? 0;
            firstNameCounts.set(contact.firstName, existingCount + 1);
        }

        const duplicateNames = new Set<string>();
        for (const [firstName, count] of firstNameCounts.entries()) {
            if (count > 1) {
                duplicateNames.add(firstName);
            }
        }

        return duplicateNames;
    }

    // Formats the full status line shown in the header based on list size and naming rules.
    function getContactLabel(contacts: ParsedContact[], duplicates: Set<string>): string {
        if (contacts.length === 0) {
            return 'No selected contacts';
        }

        if (contacts.length === 1) {
            return formatSingleContact(contacts[0]);
        }

        return formatMultipleContacts(contacts, duplicates);
    }

    // Formats the single-contact case as first and last name.
    function formatSingleContact(contact: ParsedContact): string {
        return contact.lastName.length > 0
            ? `${contact.firstName} ${contact.lastName}`
            : contact.firstName;
    }

    // Formats a contact for multi-contact labels, disambiguating only duplicated first names.
    function formatMultiContactName(contact: ParsedContact, duplicates: Set<string>): string {
        if (duplicates.has(contact.firstName) && contact.lastName.length > 0) {
            return `${contact.firstName} ${contact.lastName}`;
        }

        return contact.firstName;
    }

    // Produces the multi-contact label with either up to cutoff names or an "N others" suffix.
    function formatMultipleContacts(contacts: ParsedContact[], duplicates: Set<string>): string {
        if (contacts.length <= CONTACT_LABEL_CUTOFF_COUNT) {
            const formattedNames = contacts.map((contact) =>
                formatMultiContactName(contact, duplicates)
            );
            return joinWithAmpersand(formattedNames);
        }

        const visibleNameCount = Math.max(CONTACT_LABEL_CUTOFF_COUNT - 1, 1);
        const visibleNames = contacts
            .slice(0, visibleNameCount)
            .map((contact) => formatMultiContactName(contact, duplicates));
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
