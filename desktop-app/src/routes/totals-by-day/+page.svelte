<script lang="ts">
    import MetricStackedBarChart from '../../components/MetricStackedBarChart.svelte';
    import ResultGrid from '../../components/ResultGrid.svelte';
    import type { GridColumn } from '../../types';

    const seriesColors = [
        '#0f62fe',
        '#24a148',
        '#8a3ffc',
        '#ff832b',
        '#007d79',
        '#fa4d56',
        '#a56eff'
    ];

    function getStackedChartProps({
        rows,
        columns
    }: {
        rows: Array<Record<string, unknown>>;
        columns: GridColumn[];
    }): {
        data: Array<Record<string, string | number>>;
        series: Array<{ key: string; label: string; color: string }>;
    } {
        if (!rows.length || !columns.length) {
            return { data: [], series: [] };
        }

        const dateColumn = columns.find((column) => /date/i.test(column.header)) ?? columns[0];
        if (!dateColumn) {
            return { data: [], series: [] };
        }

        const matchedSeries = columns.filter((column) => /sent\s*by/i.test(column.header));
        const seriesColumns = matchedSeries.length
            ? matchedSeries
            : columns.filter((column) => {
                  if (column.id === dateColumn.id) {
                      return false;
                  }
                  return !/total|#\s*sent$/i.test(column.header);
              });

        if (!seriesColumns.length) {
            return { data: [], series: [] };
        }

        const data = rows
            .map((row) => {
                const entry: Record<string, string | number> = {
                    date: String(row[dateColumn.id] ?? '')
                };
                for (const column of seriesColumns) {
                    entry[column.id] = Number(row[column.id] ?? 0);
                }
                return entry;
            })
            .filter((entry) => entry.date);

        const series = seriesColumns.map((column, index) => ({
            key: column.id,
            label: column.header,
            color: seriesColors[index % seriesColors.length]
        }));

        return { data, series };
    }
</script>

<ResultGrid
    title="Totals by Day"
    description="See your message totals, per person or overall, for each day you've messaged"
    command={['totals_by_day']}
    chartsClass="result-grid-charts--wide"
>
    {#snippet charts(rows, columns)}
        {@const chartProps = getStackedChartProps({ rows, columns })}
        <MetricStackedBarChart data={chartProps.data} series={chartProps.series} x="date" />
    {/snippet}
</ResultGrid>
