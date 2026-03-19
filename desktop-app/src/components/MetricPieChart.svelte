<script lang="ts">
    import { PieChart } from 'layerchart';
    import { chartColors } from '../colors';
    import '../styles/metric-pie-chart.css';
    import type { DataPoint } from '../types';

    // Public props accepted by the pie chart wrapper component.
    interface Props {
        data: DataPoint[];
        label?: string;
        innerRadius?: number;
        outerRadius?: number;
        cornerRadius?: number;
        padAngle?: number;
    }

    // Component props with defaults for chart sizing and arc styling.
    let {
        data,
        label = '',
        innerRadius = -15,
        outerRadius = 70,
        cornerRadius = 4,
        padAngle = 0.02
    }: Props = $props();
</script>

{#if data.length > 0}
    <article class="metric-pie-chart">
        <figure class="metric-pie-chart__chart">
            <PieChart
                {data}
                key="key"
                value="value"
                cRange={chartColors}
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
                <svelte:fragment slot="aboveMarks">
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
        </figure>
        <ul class="metric-pie-chart__legend" aria-label={`${label} legend`}>
            {#each data as point, index (point.key)}
                <li class="metric-pie-chart__legend-item">
                    <span
                        class="metric-pie-chart__legend-swatch"
                        style={`--legend-color: ${chartColors[index % chartColors.length]}`}
                    ></span>
                    <span class="metric-pie-chart__legend-label">{point.key}</span>
                </li>
            {/each}
        </ul>
    </article>
{/if}
