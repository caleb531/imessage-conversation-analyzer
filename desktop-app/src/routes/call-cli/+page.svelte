<script lang="ts">
    import { Button, CodeSnippet, TextInput } from 'carbon-components-svelte';
    import InlineNotification from '../../components/InlineNotification.svelte';
    import { invokeIcaCsv, MissingContactError, type IcaCsvHeader } from '../../lib/cli';

    // Raw CLI argument text entered by the user.
    let icaArgs = $state('message_totals');
    // Parsed CSV rows returned from ICA.
    let icaRows = $state<Array<Record<string, unknown>>>([]);
    // Normalized CSV header metadata returned from ICA.
    let icaHeaders = $state<IcaCsvHeader[]>([]);
    // stderr output captured from sidecar execution.
    let icaStderr = $state('');
    // User-facing error message for failed executions.
    let icaError = $state('');
    // Running flag used to disable duplicate submissions.
    let icaRunning = $state(false);
    // Final argument list after parser and contact injection normalization.
    let resolvedArgs = $state<string[]>([]);

    // Pretty-prints rows for the debug code snippet panel.
    function formatRows(rows: Array<Record<string, unknown>>) {
        return JSON.stringify(rows, null, 2);
    }

    // Runs ICA with the current argument input and updates the debug panels.
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
