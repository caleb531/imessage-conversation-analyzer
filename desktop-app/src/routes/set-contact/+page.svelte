<script lang="ts">
    import { goto } from '$app/navigation';
    import { Button } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import ContactPicker from '../../components/ContactPicker.svelte';
    import InlineNotification from '../../components/InlineNotification.svelte';
    import {
        ensureSelectedContactsLoaded,
        selectedContacts,
        setSelectedContacts
    } from '../../lib/contacts.svelte';

    let contactSelection = $state<string[]>([]);
    let buttonDisabled = $state(false);
    let buttonLabel = $state('Save contacts');
    let saveError = $state('');
    // Duration to show success message (in milliseconds) before navigating away
    let successMessageDelay = 750;

    onMount(async () => {
        await ensureSelectedContactsLoaded();
        contactSelection = [...selectedContacts.value];
    });

    async function handleSubmit(event: Event) {
        event.preventDefault();
        saveError = '';
        if (contactSelection.length === 0) {
            saveError = 'You must select at least one contact before continuing.';
            return;
        }
        buttonDisabled = true;
        buttonLabel = 'Saving…';
        try {
            await setSelectedContacts(contactSelection);
            buttonLabel = 'Saved contacts!';
            await new Promise((resolve) => setTimeout(resolve, successMessageDelay));
            await goto('/message-totals');
        } catch (error) {
            saveError = error instanceof Error ? error.message : String(error);
            buttonLabel = 'Save contacts';
            buttonDisabled = false;
        }
    }
</script>

<section class="set-contact">
    <form class="set-contact__form" onsubmit={handleSubmit}>
        <h2>Choose contacts</h2>
        <ContactPicker bind:selectedContacts={contactSelection} />
        {#if saveError}
            <InlineNotification kind="error" title="Error" subtitle={saveError} />
        {/if}
        <Button type="submit" disabled={buttonDisabled}>
            {buttonLabel}
        </Button>
    </form>
</section>
