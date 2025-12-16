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
    let savingContact = $state(false);
    let saveError = $state('');

    onMount(async () => {
        await ensureSelectedContactLoaded();
        contactSelection = get(selectedContactStore) ?? undefined;
    });

    async function handleSubmit(event: Event) {
        event.preventDefault();
        saveError = '';
        if (!contactSelection) {
            saveError = 'Select a contact before continuing.';
            return;
        }
        savingContact = true;
        try {
            await setSelectedContact(contactSelection);
            await goto('/call-cli');
        } catch (error) {
            saveError = error instanceof Error ? error.message : String(error);
        } finally {
            savingContact = false;
        }
    }
</script>

<section class="set-contact">
    <h1>Choose a contact</h1>
    <form class="set-contact__form" onsubmit={handleSubmit}>
        <ContactPicker bind:selectedContact={contactSelection} />
        {#if saveError}
            <InlineNotification kind="error" title="Cannot save contact" subtitle={saveError} />
        {/if}
        <Button type="submit" disabled={savingContact}>
            {savingContact ? 'Saving…' : 'Save contact'}
        </Button>
    </form>
</section>

<style>
    .set-contact {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        max-width: 32rem;
        margin: 0 auto;
    }

    .set-contact__form {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1.5rem;
    }
</style>
