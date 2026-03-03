<script lang="ts">
    import { Button, ComboBox, Loading } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { fetchContacts } from '../lib/contacts.svelte';
    import '../styles/contact-picker.css';
    import { getContactBaseName, getContactDisplayLabel, type Contact } from '../types';

    type ContactItem = {
        id: string;
        text: string;
        contact: Contact;
    };

    let { selectedContacts = $bindable<Contact[]>([]) } = $props();
    let contactsLoading = $state(true);
    let contactsError = $state('');
    let comboboxItems = $state<ContactItem[]>([]);
    let searchValue = $state('');
    let selectedId = $state<string | undefined>(undefined);

    const availableComboboxItems = $derived(
        comboboxItems.filter(
            (item) => !selectedContacts.some((selectedContact) => selectedContact.id === item.id)
        )
    );
    const trimmedSearch = $derived(searchValue.trim());
    const filteredCount = $derived(
        availableComboboxItems.reduce(
            (count, item) => count + (shouldFilterItem(item, trimmedSearch) ? 1 : 0),
            0
        )
    );
    const totalFilteredCount = $derived(
        comboboxItems.reduce(
            (count, item) => count + (shouldFilterItem(item, trimmedSearch) ? 1 : 0),
            0
        )
    );
    const noMatches = $derived(Boolean(trimmedSearch) && filteredCount === 0);
    const matchesAlreadySelected = $derived(
        Boolean(trimmedSearch) && totalFilteredCount > 0 && noMatches
    );

    onMount(loadContacts);

    async function loadContacts() {
        contactsLoading = true;
        contactsError = '';
        try {
            const contacts = await fetchContacts();
            updateComboboxItems(contacts);
        } catch (error) {
            contactsError = error instanceof Error ? error.message : String(error);
            updateComboboxItems([]);
        } finally {
            contactsLoading = false;
        }
    }

    // Builds duplicate-aware ComboBox items from fetched contacts.
    function updateComboboxItems(contacts: Contact[]) {
        const baseNameCounts: Record<string, number> = {};
        for (const contact of contacts) {
            const baseName = getContactBaseName(contact);
            const existingCount = baseNameCounts[baseName] ?? 0;
            baseNameCounts[baseName] = existingCount + 1;
        }

        comboboxItems = contacts.map((contact) => {
            const baseName = getContactBaseName(contact);
            const isDuplicateBaseName = (baseNameCounts[baseName] ?? 0) > 1;

            return {
                id: contact.id,
                text: getContactDisplayLabel(contact, {
                    includeDisambiguation: isDuplicateBaseName
                }),
                contact
            };
        });

        selectedContacts = selectedContacts.filter((contact) =>
            comboboxItems.some((item) => item.id === contact.id)
        );
        if (selectedId && !comboboxItems.some((item) => item.id === selectedId)) {
            selectedId = undefined;
        }
    }

    function addContact() {
        if (!selectedId) {
            return;
        }

        const selectedContactItem = comboboxItems.find((item) => item.id === selectedId);
        if (!selectedContactItem) {
            selectedId = undefined;
            searchValue = '';
            return;
        }

        if (!selectedContacts.some((contact) => contact.id === selectedContactItem.contact.id)) {
            selectedContacts = [...selectedContacts, selectedContactItem.contact];
        }

        selectedId = undefined;
        searchValue = '';
    }

    function removeContact(contactId: string) {
        selectedContacts = selectedContacts.filter((entry) => entry.id !== contactId);
    }

    function shouldFilterItem(item: ContactItem, value: string) {
        if (!value) {
            return true;
        }
        return item.text.toLowerCase().includes(value.toLowerCase());
    }

    // Returns the selected list label from current combobox data when available.
    function getSelectedContactLabel(contact: Contact): string {
        const matchingItem = comboboxItems.find((item) => item.id === contact.id);
        return matchingItem ? matchingItem.text : getContactDisplayLabel(contact);
    }

    $effect(() => {
        if (selectedId) {
            addContact();
        }
    });
</script>

<article class="contact-picker">
    {#if contactsLoading}
        <p class="contact-picker-status contact-picker-status--loading">
            <Loading withOverlay={false} />
        </p>
    {:else if contactsError}
        <p class="contact-picker-status contact-picker-status--error">{contactsError}</p>
        <Button kind="secondary" type="button" class="contact-picker-retry" on:click={loadContacts}>
            Try again
        </Button>
    {:else}
        <div class="contact-picker__container">
            <label for="contact-picker__combobox" class="bx--label">Contact</label>
            <ComboBox
                id="contact-picker__combobox"
                placeholder="Search contacts…"
                bind:selectedId
                bind:value={searchValue}
                items={availableComboboxItems}
                {shouldFilterItem}
                disabled={!availableComboboxItems.length}
            />
        </div>
        {#if !availableComboboxItems.length}
            <p class="contact-picker-status contact-picker-status--empty">
                {#if !comboboxItems.length}
                    No contacts available.
                {:else}
                    All contacts selected.
                {/if}
            </p>
        {:else if noMatches}
            <p class="contact-picker-status contact-picker-status--empty">
                {#if matchesAlreadySelected}
                    All matching contacts already selected.
                {:else}
                    No matching contacts.
                {/if}
            </p>
        {/if}
        {#if selectedContacts.length > 0}
            <h3 class="contact-picker__selected-heading">Selected Contacts</h3>
            <ul class="contact-picker__selected-list">
                {#each selectedContacts as contact (contact.id)}
                    <li class="contact-picker__selected-item">
                        <span class="contact-picker__selected-item-label"
                            >{getSelectedContactLabel(contact)}</span
                        >
                        <Button
                            kind="ghost"
                            size="small"
                            type="button"
                            class="contact-picker-remove"
                            on:click={() => removeContact(contact.id)}
                        >
                            Remove
                        </Button>
                    </li>
                {/each}
            </ul>
        {:else if !comboboxItems.length}
            <p class="contact-picker-status contact-picker-status--selection">
                No contacts selected.
            </p>
        {/if}
    {/if}
</article>
