<script lang="ts">
    import { invokeIcaCsv, MissingContactError, type IcaCsvHeader } from '$lib/cli';
    import { Grid, WillowDark } from '@svar-ui/svelte-grid';
    import { InlineNotification, Loading } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import '../styles/result-grid.css';
    import NumberCell from './NumberCell.svelte';

    interface Props {
        title: string;
        description: string;
        command: string[];
    }

    let { title, description, command }: Props = $props();

    interface GridColumn {
        id: string;
        header: string;
        width?: number;
        flexgrow?: number;
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
        return headers.map((header, index) => {
            const value = sample[header.id];
            const isNumeric = typeof value === 'number';
            return {
                id: header.id,
                header: header.original,
                flexgrow: 1,
                width: 120,
                ...(isNumeric ? { cell: NumberCell } : {})
            } satisfies GridColumn;
        });
    }

    async function loadData() {
        loading = true;
        errorMessage = '';
        try {
            const result = await invokeIcaCsv(command);
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

<section class="result-grid">
    <header>
        <h2>{title}</h2>
        <p>{description}</p>
    </header>

    {#if errorMessage}
        <InlineNotification
            kind="error"
            title={`Unable to load ${title.toLowerCase()}`}
            subtitle={errorMessage}
        />
    {:else if loading}
        <div class="result-grid__loading">
            <Loading withOverlay={false} />
        </div>
    {:else if rows.length}
        <WillowDark>
            <Grid data={rows} {columns} />
        </WillowDark>
    {:else}
        <p>No data available.</p>
    {/if}
</section>
