<script lang="ts">
    import { Button, ComboBox, Loading } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { fetchContactNames } from '../lib/contacts.svelte';
    import '../styles/contact-picker.css';

    type ContactItem = {
        id: string;
        text: string;
    };

    let { selectedContacts = $bindable<string[]>([]) } = $props();
    let contactsLoading = $state(true);
    let contactsError = $state('');
    let comboboxItems = $state<ContactItem[]>([]);
    let searchValue = $state('');
    let selectedId = $state<string | undefined>(undefined);

    const availableComboboxItems = $derived(
        comboboxItems.filter((item) => !selectedContacts.includes(item.id))
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
            const names = await fetchContactNames();
            updateComboboxItems(names);
        } catch (error) {
            contactsError = error instanceof Error ? error.message : String(error);
            updateComboboxItems([]);
        } finally {
            contactsLoading = false;
        }
    }

    function updateComboboxItems(names: string[]) {
        comboboxItems = names.map((name) => ({ id: name, text: name }));
        selectedContacts = selectedContacts.filter((contact) =>
            comboboxItems.some((item) => item.id === contact)
        );
        if (selectedId && !comboboxItems.some((item) => item.id === selectedId)) {
            selectedId = undefined;
        }
    }

    function addContact() {
        if (!selectedId) {
            return;
        }
        if (!selectedContacts.includes(selectedId)) {
            selectedContacts = [...selectedContacts, selectedId];
        }
        selectedId = undefined;
        searchValue = '';
    }

    function removeContact(contact: string) {
        selectedContacts = selectedContacts.filter((entry) => entry !== contact);
    }

    function shouldFilterItem(item: ContactItem, value: string) {
        if (!value) {
            return true;
        }
        return item.text.toLowerCase().includes(value.toLowerCase());
    }

    $effect(() => {
        if (selectedId) {
            addContact();
        }
    });
</script>

<article class="contact-picker">
    {#if contactsLoading}
        <p class="contact-picker-status"><Loading withOverlay={false} /></p>
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
                {#each selectedContacts as contact (contact)}
                    <li class="contact-picker__selected-item">
                        <span>{contact}</span>
                        <Button
                            kind="ghost"
                            size="small"
                            type="button"
                            class="contact-picker-remove"
                            on:click={() => removeContact(contact)}
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
