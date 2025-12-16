<script lang="ts">
    import { Grid, WillowDark } from '@svar-ui/svelte-grid';
    import { InlineNotification, Loading } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { MissingContactError, runMessageTotals, type IcaCsvHeader } from '../../lib/cli';

    interface GridColumn {
        id: string;
        header: string;
        width?: number;
        flexgrow?: number;
        align?: 'start' | 'center' | 'end';
    }

    let loading = $state(true);
    let errorMessage = $state('');
    let rows = $state<Array<Record<string, unknown>>>([]);
    let columns = $state<GridColumn[]>([]);

    function createColumns(
        headers: IcaCsvHeader[],
        dataRows: Array<Record<string, unknown>>
    ): GridColumn[] {
        if (headers.length === 0) {
            return [];
        }
        const sample = dataRows[0] ?? {};
        return headers.map((header) => {
            const value = sample[header.id];
            const isNumeric = typeof value === 'number';
            const isMetricColumn = header.original.trim().toLowerCase() === 'metric';
            return {
                id: header.id,
                header: header.original,
                flexgrow: isMetricColumn ? 2 : 1,
                width: isMetricColumn ? 220 : 120,
                align: isNumeric ? 'end' : 'start'
            } satisfies GridColumn;
        });
    }

    async function loadData() {
        loading = true;
        errorMessage = '';
        try {
            const result = await runMessageTotals();
            rows = result.rows;
            columns = createColumns(result.headers, result.rows);
        } catch (error) {
            if (error instanceof MissingContactError) {
                errorMessage = error.message;
            } else {
                errorMessage = error instanceof Error ? error.message : String(error);
            }
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        void loadData();
    });
</script>

<section class="message-totals">
    <h2>Message Totals</h2>

    {#if errorMessage}
        <InlineNotification
            kind="error"
            title="Unable to load message totals"
            subtitle={errorMessage}
        />
    {:else if loading}
        <div class="message-totals__loading">
            <Loading withOverlay={false} />
        </div>
    {:else if rows.length}
        <WillowDark>
            <Grid data={rows} {columns} />
        </WillowDark>
    {:else}
        <p>No message totals available.</p>
    {/if}
</section>

<style>
    .message-totals {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        padding-bottom: 2rem;
    }

    .message-totals__loading {
        display: flex;
        justify-content: center;
        padding: 3rem 0;
    }

    :global(.sv-grid) {
        min-height: 24rem;
    }
</style>
