<script lang="ts">
    import { PieChart } from 'layerchart';
    import '../styles/metrics-pie-chart.css';

    type MetricsPieChartPoint = {
        key: string;
        value: number;
    };

    export let data: MetricsPieChartPoint[] = [];
    export let label = '';
    export let colors = ['#0f62fe', '#8a3ffc', '#00cfda', '#ff0055', '#f1c21b', '#6fdc8c'];
    export let innerRadius = -15;
    export let outerRadius = 70;
    export let cornerRadius = 4;
    export let padAngle = 0.02;
</script>

{#if data.length > 0}
    <article class="metrics-pie-chart">
        <PieChart
            data={data}
            key="key"
            value="value"
            cRange={colors}
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            cornerRadius={cornerRadius}
            padAngle={padAngle}
            props={{
                arc: {
                    strokeWidth: 30
                },
                tooltip: {
                    root: {
                        classes: { root: 'layerchart-tooltip' }
                    }
                }
            }}
        >
            <svelte:fragment slot="aboveMarks" let:width let:height>
                <text
                    x={0}
                    y={0}
                    text-anchor="middle"
                    dominant-baseline="middle"
                    class="metrics-pie-chart__label"
                >
                    {label}
                </text>
            </svelte:fragment>
        </PieChart>
    </article>
{/if}
