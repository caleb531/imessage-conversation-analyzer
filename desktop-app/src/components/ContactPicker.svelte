<script lang="ts">
    import { onMount } from 'svelte';
    import { Combobox } from 'bits-ui';
    import { fetchContactNames } from '../lib/contacts';
    import '../styles/contact-picker.css';

    let { selectedContact = $bindable<string | undefined>() } = $props();
    let contactNames = $state<string[]>([]);
    let contactsLoading = $state(true);
    let contactsError = $state('');
    let searchTerm = $state('');
    let comboboxItems = $state<{ value: string; label: string }[]>([]);
    let filteredItems = $state<{ value: string; label: string }[]>([]);
    let comboboxInputEl = $state<HTMLInputElement | null>(null);

    onMount(loadContacts);

    async function loadContacts() {
        contactsLoading = true;
        contactsError = '';
        try {
            const names = await fetchContactNames();
            contactNames = names;
            updateComboboxItems(names);
            updateFilteredItems();
        } catch (error) {
            contactsError = error instanceof Error ? error.message : String(error);
            contactNames = [];
            updateComboboxItems([]);
            updateFilteredItems();
            ensureSelection();
        } finally {
            contactsLoading = false;
        }
    }

    function updateComboboxItems(names: string[]) {
        comboboxItems = names.map((name) => ({ value: name, label: name }));
    }

    function updateFilteredItems() {
        const query = searchTerm.trim().toLowerCase();
        if (!query) {
            filteredItems = comboboxItems.slice();
            return;
        }
        filteredItems = comboboxItems.filter((item) => item.label.toLowerCase().includes(query));
    }

    function ensureSelection() {
        const first = filteredItems[0];
        selectedContact = first ? first.value : undefined;
    }

    function handleInput(event: Event & { currentTarget: HTMLInputElement }) {
        comboboxInputEl = event.currentTarget;
        searchTerm = event.currentTarget.value;
        updateFilteredItems();
        ensureSelection();
    }

    function handleInputFocus(event: Event & { currentTarget: HTMLInputElement }) {
        comboboxInputEl = event.currentTarget;
    }

    function selectItem(item?: { value: string; label: string }) {
        if (!item) {
            return;
        }
        selectedContact = item.value;
        searchTerm = item.label;
        if (comboboxInputEl) {
            comboboxInputEl.value = item.label;
        }
        updateFilteredItems();
        ensureSelection();
    }

    function handleKeyDown(event: KeyboardEvent) {
        if (event.key === 'Enter') {
            comboboxInputEl = event.currentTarget as HTMLInputElement;
            event.preventDefault();
            selectItem(filteredItems[0]);
        }
    }
</script>

<article class="contact-picker">
    {#if contactsLoading}
        <p class="contact-picker-status">Loading contacts…</p>
    {:else if contactsError}
        <p class="contact-picker-status contact-picker-status--error">{contactsError}</p>
        <button type="button" class="contact-picker-retry" onclick={loadContacts}>
            Try again
        </button>
    {:else}
        <div class="contact-picker__container">
            <Combobox.Root
                type="single"
                bind:value={selectedContact}
                items={comboboxItems}
                disabled={!comboboxItems.length}
            >
                <div class="contact-picker__field">
                    <Combobox.Input
                        class="contact-picker__input"
                        placeholder="Search contacts…"
                        aria-label="Search contacts"
                        onfocus={handleInputFocus}
                        oninput={handleInput}
                        onkeydown={handleKeyDown}
                    />
                    <Combobox.Trigger
                        class="contact-picker__trigger"
                        aria-label="Toggle contacts menu"
                    >
                        <span aria-hidden="true">▾</span>
                    </Combobox.Trigger>
                </div>
                <Combobox.Portal>
                    <Combobox.Content class="contact-picker__content" sideOffset={6}>
                        <Combobox.Viewport class="contact-picker__viewport">
                            {#if filteredItems.length}
                                {#each filteredItems as item (item.value)}
                                    <Combobox.Item
                                        class="contact-picker__item"
                                        value={item.value}
                                        label={item.label}
                                        onclick={() => selectItem(item)}
                                    >
                                        {#snippet children({ selected })}
                                            <span>{item.label}</span>
                                            {#if selected}
                                                <span
                                                    class="contact-picker__check"
                                                    aria-hidden="true">✓</span
                                                >
                                            {/if}
                                        {/snippet}
                                    </Combobox.Item>
                                {/each}
                            {:else}
                                <span class="contact-picker__empty">No contacts available</span>
                            {/if}
                        </Combobox.Viewport>
                    </Combobox.Content>
                </Combobox.Portal>
            </Combobox.Root>
        </div>
        {#if !comboboxItems.length}
            <p class="contact-picker-status contact-picker-status--empty">
                No contacts are available.
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
