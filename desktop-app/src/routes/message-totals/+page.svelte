<script lang="ts">
    import ResultGrid from '../../components/ResultGrid.svelte';
    import { PieChart } from 'layerchart';

    function formatLabel(key: string) {
        if (key === 'messagesFromMe') return 'Me';
        return key.replace(/^messagesFrom/, '');
    }
</script>

<ResultGrid
    title="Message Totals"
    description="Review aggregated conversation metrics like the total number of messages sent and received."
    command={['message_totals']}
>
    {#snippet chart(rows, columns)}
        {@const metricCol = columns.find(c => c.header === 'Metric')}
        {@const totalCol = columns.find(c => c.header === 'Total')}

        {#if metricCol && totalCol}
            {@const data = rows
                .filter(r => {
                    const label = r[metricCol.id];
                    return typeof label === 'string' && label.startsWith('Messages From ');
                })
                .map(r => ({
                    key: (r[metricCol.id] as string).replace('Messages From ', ''),
                    value: Number(r[totalCol.id])
                }))
                .filter(d => d.value > 0)
                .sort((a, b) => b.value - a.value)
            }

            {#if data.length > 0}
                <div style="height: 300px; margin-bottom: 2rem; position: relative;">
                    <PieChart
                        {data}
                        key="key"
                        value="value"
                        cRange={['#0f62fe', '#8a3ffc', '#00cfda', '#ff0055', '#f1c21b', '#6fdc8c']}
                        innerRadius={-20}
                        cornerRadius={4}
                        padAngle={0.02}
                        props={{
                            tooltip: {
                                root: {
                                    classes: { root: 'layerchart-tooltip' }
                                }
                            }
                        }}
                    />
                </div>
            {/if}
        {/if}
    {/snippet}

<style>
    :global(.layerchart-tooltip) {
        position: absolute;
        z-index: 9999;
        pointer-events: none;
        background: rgba(22, 22, 22, 0.9);
        border: 1px solid #393939;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.5);
    }
</style>
</ResultGrid>
