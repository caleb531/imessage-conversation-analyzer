<script lang="ts">
    import { BarChart } from 'layerchart';
    import '../styles/metrics-bar-chart.css';
    import type { DataPoint } from '../types';

    let {
        data,
        x = 'key',
        y = 'value'
    }: { data: DataPoint[]; x?: string; y?: string; color?: string } = $props();
</script>

{#if data.length > 0}
    <article class="metrics-bar-chart">
        <BarChart
            {data}
            {x}
            {y}
            bandPadding={0.3}
            props={{
                bars: {
                    radius: 4
                },
                xAxis: {
                    tickLabelProps: {
                        class: 'emoji-tick-label'
                    }
                },
                yAxis: {
                    ticks: 5
                },
                tooltip: {
                    root: {
                        classes: { root: 'layerchart-tooltip' }
                    },
                    item: {
                        label: ''
                    }
                }
            }}
        />
    </article>
{/if}
