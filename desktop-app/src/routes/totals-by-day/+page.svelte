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

    const dateLabelFormatter = new Intl.DateTimeFormat('en-US', {
        month: 'numeric',
        day: 'numeric'
    });

    function formatDateTick(value: string | number): string {
        const parsedDate = parseDateValue(value);
        if (!parsedDate) {
            return String(value ?? '');
        }
        return dateLabelFormatter.format(parsedDate);
    }

    function parseDateValue(value: unknown): Date | null {
        const input = String(value ?? '').trim();
        if (!input) {
            return null;
        }

        const isoDateOnlyMatch = input.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (isoDateOnlyMatch) {
            const [, yearString, monthString, dayString] = isoDateOnlyMatch;
            const year = Number(yearString);
            const monthIndex = Number(monthString) - 1;
            const day = Number(dayString);
            const parsed = new Date(year, monthIndex, day);
            if (
                parsed.getFullYear() === year &&
                parsed.getMonth() === monthIndex &&
                parsed.getDate() === day
            ) {
                return parsed;
            }
            return null;
        }

        const parsed = new Date(input);
        return Number.isNaN(parsed.getTime()) ? null : parsed;
    }

    function getStackedChartProps({
        rows,
        columns
    }: {
        rows: Array<Record<string, unknown>>;
        columns: GridColumn[];
    }): {
        data: Array<Record<string, string | number>>;
        series: Array<{ key: string; label: string; color: string }>;
        xGroupLabels: Array<{ label: string; startIndex: number }>;
    } {
        if (!rows.length || !columns.length) {
            return { data: [], series: [], xGroupLabels: [] };
        }

        const dateColumn = columns.find((column) => /date/i.test(column.header)) ?? columns[0];
        if (!dateColumn) {
            return { data: [], series: [], xGroupLabels: [] };
        }

        const matchedSeries = columns.filter((column) => /sent\s*by/i.test(column.header));
        const candidateSeriesColumns = matchedSeries.length
            ? matchedSeries
            : columns.filter((column) => {
                  if (column.id === dateColumn.id) {
                      return false;
                  }
                  return !/total|#\s*sent$/i.test(column.header);
              });

        const seriesColumns =
            candidateSeriesColumns.length <= 2
                ? candidateSeriesColumns
                : [...candidateSeriesColumns]
                      .sort((left, right) => {
                          const leftTotal = rows.reduce(
                              (sum, row) => sum + Number(row[left.id] ?? 0),
                              0
                          );
                          const rightTotal = rows.reduce(
                              (sum, row) => sum + Number(row[right.id] ?? 0),
                              0
                          );
                          return rightTotal - leftTotal;
                      })
                      .slice(0, 2);

        if (!seriesColumns.length) {
            return { data: [], series: [], xGroupLabels: [] };
        }

        const dataWithYear = rows
            .map((row) => {
                const rawDate = String(row[dateColumn.id] ?? '').trim();
                if (!rawDate) {
                    return null;
                }

                const parsedDate = parseDateValue(rawDate);
                const yearLabel = parsedDate ? String(parsedDate.getFullYear()) : '';

                const entry: Record<string, string | number> = {
                    date: rawDate
                };

                for (const column of seriesColumns) {
                    entry[column.id] = Number(row[column.id] ?? 0);
                }

                return {
                    entry,
                    yearLabel
                };
            })
            .filter((item): item is { entry: Record<string, string | number>; yearLabel: string } =>
                Boolean(item)
            );

        const data = dataWithYear.map((item) => item.entry);

        const xGroupLabels = dataWithYear.reduce<Array<{ label: string; startIndex: number }>>(
            (groups, item, index) => {
                if (!item.yearLabel) {
                    return groups;
                }

                const previousGroup = groups[groups.length - 1];
                if (!previousGroup || previousGroup.label !== item.yearLabel) {
                    groups.push({ label: item.yearLabel, startIndex: index });
                }
                return groups;
            },
            []
        );

        const series = seriesColumns.map((column, index) => ({
            key: column.id,
            label: column.header,
            color: seriesColors[index % seriesColors.length]
        }));

        return { data, series, xGroupLabels };
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
        <MetricStackedBarChart
            data={chartProps.data}
            series={chartProps.series}
            x="date"
            xGroupLabels={chartProps.xGroupLabels}
            xTickFormat={formatDateTick}
        />
    {/snippet}
</ResultGrid>
