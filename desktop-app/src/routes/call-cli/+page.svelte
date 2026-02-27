<script lang="ts">
    import { Button, CodeSnippet, TextInput } from 'carbon-components-svelte';
    import InlineNotification from '../../components/InlineNotification.svelte';
    import { invokeIcaCsv, MissingContactError, type IcaCsvHeader } from '../../lib/cli';

    let icaArgs = $state('message_totals');
    let icaRows = $state<Array<Record<string, unknown>>>([]);
    let icaHeaders = $state<IcaCsvHeader[]>([]);
    let icaStderr = $state('');
    let icaError = $state('');
    let icaRunning = $state(false);
    let resolvedArgs = $state<string[]>([]);

    function formatRows(rows: Array<Record<string, unknown>>) {
        return JSON.stringify(rows, null, 2);
    }

    async function runSidecar(event: Event) {
        event.preventDefault();
        icaRunning = true;
        icaError = '';
        icaRows = [];
        icaHeaders = [];
        icaStderr = '';
        resolvedArgs = [];
        try {
            const result = await invokeIcaCsv(icaArgs);
            resolvedArgs = result.args;
            icaRows = result.rows;
            icaHeaders = result.headers;
            icaStderr = result.stderr;
        } catch (error) {
            if (error instanceof MissingContactError) {
                icaError = error.message;
            } else {
                icaError = error instanceof Error ? error.message : String(error);
            }
        } finally {
            icaRunning = false;
        }
    }
</script>

<section class="call-cli">
    <form class="call-cli__form" onsubmit={runSidecar}>
        <h2>Call ICA CLI</h2>
        <TextInput
            labelText="CLI arguments"
            id="sidecar-args"
            placeholder="message_totals"
            bind:value={icaArgs}
            autocomplete="off"
        />
        <Button type="submit" disabled={icaRunning}>
            {icaRunning ? 'Running…' : 'Call CLI'}
        </Button>
    </form>

    {#if resolvedArgs.length}
        <CodeSnippet type="multi">{resolvedArgs.join(' ')}</CodeSnippet>
    {/if}

    {#if icaHeaders.length}
        <CodeSnippet type="multi">{JSON.stringify(icaHeaders, null, 2)}</CodeSnippet>
    {/if}

    {#if icaRows.length}
        <CodeSnippet type="multi">{formatRows(icaRows)}</CodeSnippet>
    {/if}

    {#if icaStderr}
        <pre class="call-cli__error-log">{icaStderr}</pre>
    {/if}

    {#if icaError}
        <InlineNotification kind="error" title="ICA error" subtitle={icaError} />
    {/if}
</section>

<style>
    .call-cli {
        display: flex;
        flex-direction: column;
        max-width: 48rem;
        margin: 0 auto;
    }

    .call-cli__error-log {
        padding: 1rem;
        background-color: var(--color-surface-elevated-subtle);
        border-radius: 0.25rem;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.875rem;
        overflow-x: auto;
    }
</style>
