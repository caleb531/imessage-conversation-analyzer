<script lang="ts">
    import { goto } from '$app/navigation';
    import { Button, CodeSnippet, InlineNotification, TextInput } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { get } from 'svelte/store';
    import {
        ensureSelectedContactLoaded,
        selectedContact as selectedContactStore
    } from '../../lib/contactStore';
    import { runIcaSidecar } from '../../lib/sidecar';

    let icaArgs = $state('--help');
    let icaOutput = $state('');
    let icaError = $state('');
    let icaRunning = $state(false);
    let showMissingContact = $state(false);

    onMount(async () => {
        await ensureSelectedContactLoaded();
        const currentContact = get(selectedContactStore);
        if (!currentContact) {
            showMissingContact = true;
            await goto('/set-contact');
        }
    });

    function splitArgs(input: string): string[] {
        // Support very small subset of shell quoting for convenience in the UI.
        return (
            input
                .match(/(?:"[^"]*"|'[^']*'|\S+)/g)
                ?.map((token) => token.replace(/^["']|["']$/g, '')) ?? []
        );
    }

    async function runSidecar(event: Event) {
        event.preventDefault();
        icaRunning = true;
        icaOutput = '';
        icaError = '';
        try {
            const args = icaArgs.trim() ? splitArgs(icaArgs) : [];
            const result = await runIcaSidecar(args);
            icaOutput = result.stdout.trimEnd();
            icaError = result.stderr.trimEnd();
        } catch (error) {
            icaError = error instanceof Error ? error.message : String(error);
        } finally {
            icaRunning = false;
        }
    }
</script>

<section class="call-cli">
    <h1>Run ICA sidecar</h1>
    {#if showMissingContact}
        <InlineNotification
            kind="error"
            title="No contact selected"
            subtitle="Choose a contact before running the sidecar."
        />
    {/if}
    <form class="call-cli__form" onsubmit={runSidecar}>
        <TextInput
            labelText="CLI arguments"
            id="sidecar-args"
            placeholder="--help"
            bind:value={icaArgs}
            autocomplete="off"
        />
        <Button type="submit" disabled={icaRunning}>
            {icaRunning ? 'Running…' : 'Run ica-sidecar'}
        </Button>
    </form>

    {#if icaOutput}
        <CodeSnippet type="multi">{icaOutput}</CodeSnippet>
    {/if}

    {#if icaError}
        <pre class="call-cli__error-log">{icaError}</pre>
    {/if}
</section>

<style>
    .call-cli {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        max-width: 48rem;
        margin: 0 auto;
    }

    .call-cli__form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .call-cli__error-log {
        padding: 1rem;
        background-color: rgba(255, 255, 255, 0.04);
        border-radius: 0.25rem;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.875rem;
        overflow-x: auto;
    }
</style>
