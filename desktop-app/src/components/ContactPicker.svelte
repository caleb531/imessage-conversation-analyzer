<script lang="ts">
    import { Button, ComboBox, Loading } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { fetchContactNames } from '../lib/contacts';
    import '../styles/contact-picker.css';

    type ContactItem = {
        id: string;
        text: string;
    };

    let { selectedContact = $bindable<string | undefined>() } = $props();
    let contactsLoading = $state(true);
    let contactsError = $state('');
    let comboboxItems = $state<ContactItem[]>([]);
    let searchValue = $state('');

    const trimmedSearch = $derived(searchValue.trim());
    const filteredCount = $derived(
        comboboxItems.reduce(
            (count, item) => count + (shouldFilterItem(item, trimmedSearch) ? 1 : 0),
            0
        )
    );
    const noMatches = $derived(Boolean(trimmedSearch) && filteredCount === 0);

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
        if (!comboboxItems.some((item) => item.id === selectedContact)) {
            selectedContact = undefined;
        }
    }

    function shouldFilterItem(item: ContactItem, value: string) {
        if (!value) {
            return true;
        }
        return item.text.toLowerCase().includes(value.toLowerCase());
    }
</script>

<article class="contact-picker">
    {#if contactsLoading}
        <p class="contact-picker-status"><Loading /></p>
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
                bind:selectedId={selectedContact}
                bind:value={searchValue}
                items={comboboxItems}
                {shouldFilterItem}
                disabled={!comboboxItems.length}
            />
        </div>
        {#if !comboboxItems.length}
            <p class="contact-picker-status contact-picker-status--empty">
                No contacts are available.
            </p>
        {:else if noMatches}
            <p class="contact-picker-status contact-picker-status--empty">
                No contacts match "{trimmedSearch}".
            </p>
        {/if}
        {#if selectedContact}
            <p class="contact-picker-status contact-picker-status--selection">
                Selected contact: {selectedContact}
            </p>
        {:else}
            <p class="contact-picker-status contact-picker-status--selection">
                No contact selected.
            </p>
        {/if}
    {/if}
</article>
