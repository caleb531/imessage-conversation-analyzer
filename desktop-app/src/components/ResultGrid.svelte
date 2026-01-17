<script lang="ts">
    import { invokeIcaCsv, MissingContactError, type IcaCsvHeader } from '$lib/cli';
    import { Grid, WillowDark } from '@svar-ui/svelte-grid';
    import { InlineNotification, Loading } from 'carbon-components-svelte';
    import { onMount, type Snippet } from 'svelte';
    import '../styles/result-grid.css';
    import DateCell from './DateCell.svelte';
    import NumberCell from './NumberCell.svelte';

    interface GridColumn {
        id: string;
        header: string;
        width?: number;
        flexgrow?: number;
    }

    interface Props {
        title: string;
        description: string;
        command: string[];
        chart?: Snippet<[Array<Record<string, unknown>>, GridColumn[]]>;
    }

    let { title, description, command, chart }: Props = $props();

    let loading = $state(true);
    let errorMessage = $state('');
    let rows = $state<Array<Record<string, unknown>>>([]);
    let columns = $state<GridColumn[]>([]);

    const cellFormatters = [
        {
            pattern: /^\d+$/,
            component: NumberCell
        },
        {
            pattern: /^\d{4}-\d{2}-\d{2}$/,
            component: DateCell
        }
    ];

    function getValueFormatter(value: string | number) {
        for (const formatter of cellFormatters) {
            if (formatter.pattern.test(String(value))) {
                return formatter.component;
            }
        }
        return null;
    }

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
            const ValueFormatter = getValueFormatter(value as string | number);
            return {
                id: header.id,
                header: header.original,
                flexgrow: 1,
                width: 120,
                ...(ValueFormatter ? { cell: ValueFormatter } : {})
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
        {#if chart}
             <div aria-label="Chart area" role="img">
                {@render chart(rows, columns)}
             </div>
        {/if}
        <WillowDark>
            <Grid data={rows} {columns} />
        </WillowDark>
    {:else}
        <p>No data available.</p>
    {/if}
</section>
