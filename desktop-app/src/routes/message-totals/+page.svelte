<script lang="ts">
    import MetricPieChart from '../../components/MetricPieChart.svelte';
    import ResultGrid from '../../components/ResultGrid.svelte';
    import type { DataPoint, GridColumn } from '../../types';

    function getChartDataFromMetrics({
        rows,
        columns,
        columnNamePattern,
        columnNameFormatter
    }: {
        rows: Array<Record<string, unknown>>;
        columns: GridColumn[];
        columnNamePattern: RegExp;
        columnNameFormatter: (s: string) => string;
    }): DataPoint[] {
        const metricCol = columns.find((column) => column.header === 'Metric');
        const totalCol = columns.find((column) => column.header === 'Total');
        if (!metricCol || !totalCol) {
            return [];
        }
        return rows
            .filter((row) => {
                const label = row[metricCol.id];
                return typeof label === 'string' && columnNamePattern.test(label);
            })
            .map((row) => {
                return {
                    key: columnNameFormatter(String(row[metricCol.id])),
                    value: Number(row[totalCol.id])
                };
            })
            .filter((dataPoint) => dataPoint.value > 0)
            .sort((a, b) => b.value - a.value);
    }
</script>

<ResultGrid
    title="Message Totals"
    description="Review aggregated conversation metrics like the total number of messages sent and received."
    command={['message_totals']}
>
    {#snippet charts(rows, columns)}
        <MetricPieChart
            data={getChartDataFromMetrics({
                rows,
                columns,
                columnNamePattern: /Messages From /i,
                columnNameFormatter: (s) => s.replace(/Messages From /i, '')
            })}
            label="Messages"
        />
        <MetricPieChart
            data={getChartDataFromMetrics({
                rows,
                columns,
                columnNamePattern: /Reactions From /i,
                columnNameFormatter: (s) => s.replace(/Reactions From /i, '')
            })}
            label="Reactions"
        />
    {/snippet}
</ResultGrid>
