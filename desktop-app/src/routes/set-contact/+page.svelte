<script lang="ts">
    import { goto } from '$app/navigation';
    import { Button, InlineNotification } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { get } from 'svelte/store';
    import ContactPicker from '../../components/ContactPicker.svelte';
    import {
        ensureSelectedContactLoaded,
        selectedContact as selectedContactStore,
        setSelectedContact
    } from '../../lib/contactStore';

    let contactSelection = $state<string | undefined>(undefined);
    let buttonDisabled = $state(false);
    let buttonLabel = $state('Save contact');
    let saveError = $state('');
    // Duration to show success message (in milliseconds) before navigating away
    let successMessageDelay = 750;

    onMount(async () => {
        await ensureSelectedContactLoaded();
        contactSelection = get(selectedContactStore) ?? undefined;
    });

    async function handleSubmit(event: Event) {
        event.preventDefault();
        saveError = '';
        if (!contactSelection) {
            saveError = 'You must select a contact before continuing.';
            return;
        }
        buttonDisabled = true;
        buttonLabel = 'Saving…';
        try {
            await setSelectedContact(contactSelection);
            buttonLabel = 'Saved contact!';
            await new Promise((resolve) => setTimeout(resolve, successMessageDelay));
            await goto('/call-cli');
        } catch (error) {
            saveError = error instanceof Error ? error.message : String(error);
            buttonLabel = 'Save contact';
            buttonDisabled = false;
        }
    }
</script>

<section class="set-contact">
    <form class="set-contact__form" onsubmit={handleSubmit}>
        <h2>Choose a contact</h2>
        <ContactPicker bind:selectedContact={contactSelection} />
        {#if saveError}
            <InlineNotification kind="error" title="Error" subtitle={saveError} />
        {/if}
        <Button type="submit" disabled={buttonDisabled}>
            {buttonLabel}
        </Button>
    </form>
</section>

<style>
    .set-contact {
        display: flex;
        flex-direction: column;
        max-width: 32rem;
        margin: 0 auto;
    }
</style>
