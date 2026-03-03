<script lang="ts">
    import { onMount } from 'svelte';
    import ContactPicker from '../../components/ContactPicker.svelte';
    import InlineNotification from '../../components/InlineNotification.svelte';
    import {
        ensureSelectedContactsLoaded,
        selectedContacts,
        setSelectedContacts
    } from '../../lib/contacts.svelte';
    import type { Contact } from '../../types';

    // Tracks the contacts selected in the picker prior to persistence.
    let pickerSelectedContacts = $state<Contact[]>([]);
    // Tracks the latest persistence failure message for inline display.
    let saveError = $state('');
    // Indicates that initial contact state has been loaded from persisted storage.
    let hasInitializedSelection = $state(false);
    // Tracks the most recent save request number to ignore stale async completion.
    let saveRequestVersion = 0;

    onMount(async () => {
        await ensureSelectedContactsLoaded();
        pickerSelectedContacts = [...selectedContacts.value];
        hasInitializedSelection = true;
    });

    // Persists the latest contact selection and only applies results from the newest request.
    async function persistSelection(contacts: Contact[]) {
        // Capture the current value of the request version before awaiting
        // so we can ignore stale failures from older saves that finish after newer ones.
        const requestVersion = saveRequestVersion + 1;
        saveRequestVersion = requestVersion;
        saveError = '';

        try {
            await setSelectedContacts(contacts);
        } catch (error) {
            if (requestVersion === saveRequestVersion) {
                saveError = error instanceof Error ? error.message : String(error);
            }
        }
    }

    // Automatically persists contacts whenever picker selection changes after initial load.
    $effect(() => {
        if (!hasInitializedSelection) {
            return;
        }

        void persistSelection([...pickerSelectedContacts]);
    });
</script>

<section class="set-contacts">
    <form class="set-contacts__form" onsubmit={(event) => event.preventDefault()}>
        <h2>Choose contacts</h2>
        <ContactPicker bind:selectedContacts={pickerSelectedContacts} />
        <p class="set-contacts__note">Changes are automatically saved</p>
        {#if saveError}
            <InlineNotification kind="error" title="Error" subtitle={saveError} />
        {/if}
    </form>
</section>

<style>
    .set-contacts__note {
        font-style: italic;
        color: var(--color-text-subtle);
        margin: 0;
        font-size: 0.875rem;
    }
</style>
