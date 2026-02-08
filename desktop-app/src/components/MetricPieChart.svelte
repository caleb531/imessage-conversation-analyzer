<script lang="ts">
    import { PieChart } from 'layerchart';
    import '../styles/metric-pie-chart.css';
    import type { DataPoint } from '../types';

    export let data: DataPoint[];
    export let label = '';
    export let colors = ['#0f62fe', '#8a3ffc', '#00cfda', '#ff0055', '#f1c21b', '#6fdc8c'];
    export let innerRadius = -15;
    export let outerRadius = 70;
    export let cornerRadius = 4;
    export let padAngle = 0.02;
</script>

{#if data.length > 0}
    <article class="metric-pie-chart">
        <div class="metric-pie-chart__chart">
            <PieChart
                {data}
                key="key"
                value="value"
                cRange={colors}
                {innerRadius}
                {outerRadius}
                {cornerRadius}
                {padAngle}
                props={{
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
                        class="metric-pie-chart__label"
                    >
                        {label}
                    </text>
                </svelte:fragment>
            </PieChart>
        </div>
        <ul class="metric-pie-chart__legend" aria-label={`${label} legend`}>
            {#each data as point, index}
                <li class="metric-pie-chart__legend-item">
                    <span
                        class="metric-pie-chart__legend-swatch"
                        style={`--legend-color: ${colors[index % colors.length]}`}
                    ></span>
                    <span class="metric-pie-chart__legend-label">{point.key}</span>
                </li>
            {/each}
        </ul>
    </article>
{/if}
