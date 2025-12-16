<script lang="ts">
    import { Button, CodeSnippet, TextInput } from 'carbon-components-svelte';
    import ContactPicker from '../components/ContactPicker.svelte';
    import { runIcaSidecar } from '../lib/sidecar';
    import '../styles/page.css';

    let icaArgs = $state('--help');
    let icaOutput = $state('');
    let icaError = $state('');
    let icaRunning = $state(false);
    let selectedContact = $state<string | undefined>(undefined);

    function splitArgs(input: string): string[] {
        // Support very small subset of shell quoting for convenience in the UI.
        return (
            input
                .match(/(?:"[^"]*"|'[^']*'|\S+)/g)
                ?.map((token) => token.replace(/^['"]|['"]$/g, '')) ?? []
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

<h1>iMessage Conversation Analyzer</h1>
<section class="contacts-section">
    <h2>Choose a contact</h2>
    <form onsubmit={(event) => event.preventDefault()}>
        <ContactPicker bind:selectedContact />
    </form>
</section>
<section>
    <form onsubmit={runSidecar}>
        <TextInput
            labelText="CLI Arguments"
            id="sidecar-args"
            placeholder="--help"
            bind:value={icaArgs}
            autocomplete="off"
        />
        <Button type="submit" disabled={icaRunning}>
            {icaRunning ? 'Running…' : 'Run ica-sidecar'}
        </Button>
    </form>
</section>

{#if icaOutput}
    <CodeSnippet type="multi">{icaOutput}</CodeSnippet>
{/if}

{#if icaError}
    <pre class="error-log">{icaError}</pre>
{/if}
