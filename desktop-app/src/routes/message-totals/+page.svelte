<script lang="ts">
    import ResultGrid from '../../components/ResultGrid.svelte';
    import MetricsPieChart from '../../components/MetricsPieChart.svelte';
</script>

<ResultGrid
    title="Message Totals"
    description="Review aggregated conversation metrics like the total number of messages sent and received."
    command={['message_totals']}
>
    {#snippet charts(rows, columns)}
        {@const metricCol = columns.find(c => c.header === 'Metric')}
        {@const totalCol = columns.find(c => c.header === 'Total')}

        {#if metricCol && totalCol}
            {@const messageMetrics = rows
                .filter((row) => {
                    const label = row[metricCol.id];
                    return typeof label === 'string' && label.startsWith('Messages From ');
                })
                .map((row) => ({
                    key: String(row[metricCol.id]).replace('Messages From ', ''),
                    value: Number(row[totalCol.id])
                }))
                .filter((dataPoint) => dataPoint.value > 0)
                .sort((a, b) => b.value - a.value)
            }
            {@const reactionMetrics = rows
                .filter((row) => {
                    const label = row[metricCol.id];
                    return typeof label === 'string' && label.startsWith('Reactions From ');
                })
                .map((row) => ({
                    key: String(row[metricCol.id]).replace('Messages From ', ''),
                    value: Number(row[totalCol.id])
                }))
                .filter(d => d.value > 0)
                .sort((a, b) => b.value - a.value)
            }

            {#if messageMetrics.length > 0}
                <MetricsPieChart data={messageMetrics} label="Messages" />
            {/if}
            {#if reactionMetrics.length > 0}
                <MetricsPieChart data={reactionMetrics} label="Reactions" />
            {/if}
        {/if}
    {/snippet}
</ResultGrid>
