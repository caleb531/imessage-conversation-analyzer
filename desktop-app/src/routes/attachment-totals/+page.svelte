<script lang="ts">
    import MetricBarChart from '../../components/MetricBarChart.svelte';
    import ResultGrid from '../../components/ResultGrid.svelte';
    import type { DataPoint, GridColumn } from '../../types';

    function getChartData({
        rows,
        columns
    }: {
        rows: Array<Record<string, unknown>>;
        columns: GridColumn[];
    }): DataPoint[] {
        if (!columns.length || !rows.length) return [];

        // Result usually matches "Type" and "Total"
        let keyCol = columns.find((c) => /Type/i.test(c.header));
        let valueCol = columns.find((c) => /Count|Total/i.test(c.header));

        // Fallback: Use first and second columns if named columns not found
        if (!keyCol && columns.length > 0) keyCol = columns[0];
        if (!valueCol && columns.length > 1) valueCol = columns[1];

        if (!keyCol || !valueCol) return [];

        return rows
            .map((row) => {
                return {
                    key: String(row[keyCol!.id]),
                    value: Number(row[valueCol!.id])
                };
            })
            .sort((a, b) => b.value - a.value);
    }
</script>

<ResultGrid
    title="Attachment Totals"
    description="Review aggregated totals for each type of attachment in your conversation."
    command={['attachment_totals']}
>
    {#snippet charts(rows, columns)}
        <MetricBarChart data={getChartData({ rows, columns })} orientation="horizontal" />
    {/snippet}
</ResultGrid>
