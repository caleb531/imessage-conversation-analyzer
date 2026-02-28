<script lang="ts">
    import MetricStackedBarChart from '../../components/MetricStackedBarChart.svelte';
    import ResultGrid from '../../components/ResultGrid.svelte';
    import type { GridColumn } from '../../types';

    const seriesColors = [
        'var(--color-chart-series-1)',
        'var(--color-chart-series-2)',
        'var(--color-chart-series-3)',
        'var(--color-chart-series-4)',
        'var(--color-chart-series-5)',
        'var(--color-chart-series-6)',
        'var(--color-chart-series-7)'
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
        if (!columns.length || !rows.length) {
            return { data: [], series: [] };
        }

        const keyColumn = columns.find((column) => /Emoji/i.test(column.header)) ?? columns[0];
        if (!keyColumn) {
            return { data: [], series: [] };
        }

        const matchedSeries = columns.filter(
            (column) => /count\s*from/i.test(column.header) || /^countFrom/i.test(column.id)
        );
        const seriesColumns = matchedSeries.length
            ? matchedSeries
            : columns.filter((column) => {
                  if (column.id === keyColumn.id) {
                      return false;
                  }
                  return !/^count$/i.test(column.header) && !/^total$/i.test(column.header);
              });

        if (!seriesColumns.length) {
            return { data: [], series: [] };
        }

        const data = rows
            .map((row) => {
                const keyValue = String(row[keyColumn.id] ?? '').trim();
                if (!keyValue) {
                    return null;
                }

                const entry: Record<string, string | number> = {
                    key: keyValue
                };

                for (const column of seriesColumns) {
                    entry[column.id] = Number(row[column.id] ?? 0);
                }

                return entry;
            })
            .filter((item): item is Record<string, string | number> => Boolean(item))
            .sort((left, right) => {
                const leftTotal = seriesColumns.reduce(
                    (sum, column) => sum + Number(left[column.id] ?? 0),
                    0
                );
                const rightTotal = seriesColumns.reduce(
                    (sum, column) => sum + Number(right[column.id] ?? 0),
                    0
                );
                return rightTotal - leftTotal;
            });

        const series = seriesColumns.map((column, index) => ({
            key: column.id,
            label: column.header,
            color: seriesColors[index % seriesColors.length]
        }));

        return { data, series };
    }
</script>

<ResultGrid
    title="Most Frequent Emojis"
    description="See which emojis are used most frequently in your conversation."
    command={['most_frequent_emojis']}
>
    {#snippet charts(rows, columns)}
        {@const chartProps = getStackedChartProps({ rows, columns })}
        <MetricStackedBarChart
            data={chartProps.data}
            series={chartProps.series}
            labelType="emoji"
            showAllCategoryLabels
        />
    {/snippet}
</ResultGrid>
