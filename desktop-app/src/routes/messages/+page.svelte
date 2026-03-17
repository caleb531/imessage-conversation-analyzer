<script lang="ts">
    import { chartColors } from '../../colors';
    import MetricPieChart from '../../components/MetricPieChart.svelte';
    import MetricSection from '../../components/MetricSection.svelte';
    import MetricStackedBarChart from '../../components/MetricStackedBarChart.svelte';
    import ResultGrid from '../../components/ResultGrid.svelte';
    import type { DataPoint, GridColumn } from '../../types';

    // Extracts sorted pie-chart datapoints from metric/total table rows.
    function getChartDataFromMetrics({
        rows,
        columns,
        columnNamePattern,
        columnNameFormatter
    }: {
        rows: Array<Record<string, unknown>>;
        columns: GridColumn[];
        columnNamePattern: RegExp;
        columnNameFormatter: (_input: string) => string;
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

    // Formatter used for compact month/day x-axis labels.
    const dateLabelFormatter = new Intl.DateTimeFormat('en-US', {
        month: 'numeric',
        day: 'numeric'
    });

    // Formats axis tick values into short date labels.
    function formatDateTick(value: string | number): string {
        const parsedDate = parseDateValue(value);
        if (!parsedDate) {
            return String(value ?? '');
        }
        return dateLabelFormatter.format(parsedDate);
    }

    // Parses mixed date inputs into valid Date objects when possible.
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

    // Builds chart series, data points, and year boundary labels from grid data.
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

        const seriesColumns = candidateSeriesColumns;

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
            color: chartColors[index % chartColors.length]
        }));

        return { data, series, xGroupLabels };
    }
</script>

<MetricSection title="Messages" level={2}>
    <MetricSection
        title="Summary"
        description="Review aggregated conversation metrics like the total number of messages sent and received."
        level={3}
    >
        <ResultGrid
            command={['message_totals']}
            layout="horizontal"
            chartLayout="vertical"
            dateFilterPersistenceKey="messages"
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
    </MetricSection>

    <MetricSection
        title="Totals by Day"
        description="See your message totals, per person or overall, for each day you've messaged"
        level={3}
    >
        <ResultGrid
            command={['totals_by_day']}
            chartsClass="result-grid-charts--wide"
            dateFilterPersistenceKey="totals-by-day"
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
    </MetricSection>
</MetricSection>
