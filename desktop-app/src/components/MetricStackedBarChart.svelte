<script lang="ts">
    import { BarChart } from 'layerchart';
    import '../styles/metric-stacked-bar-chart.css';

    type StackedDatum = Record<string, string | number>;
    type StackedSeries = { key: string; label: string; color?: string };

    let {
        data,
        series,
        x = 'key',
        bandPadding = 0.2,
        labelType = 'string',
        minLabelWidth = 90,
        barWidth = 6,
        showLegend = true
    }: {
        data: StackedDatum[];
        series: StackedSeries[];
        x?: string;
        bandPadding?: number;
        labelType?: 'string' | 'emoji';
        minLabelWidth?: number;
        barWidth?: number;
        showLegend?: boolean;
    } = $props();

    let containerWidth = $state(0);

    const labelClass = $derived(labelType === 'emoji' ? 'emoji-tick-label' : 'text-tick-label');

    const tickCount = $derived.by(() => {
        if (containerWidth <= 0) {
            return 4;
        }
        return Math.max(2, Math.floor(containerWidth / minLabelWidth));
    });

    const chartWidth = $derived.by(() => {
        if (data.length === 0) {
            return containerWidth;
        }
        return Math.max(containerWidth, data.length * barWidth);
    });

    const axisProps = $derived.by(() => ({
        xAxis: {
            ticks: tickCount,
            tickLabelProps: {
                class: labelClass
            }
        },
        yAxis: {
            ticks: 5
        }
    }));

    const maxStackValue = $derived.by(() => {
        if (data.length === 0 || series.length === 0) {
            return 0;
        }
        return data.reduce((maxValue, datum) => {
            const total = series.reduce((sum, item) => {
                const value = Number(datum[item.key] ?? 0);
                return sum + (Number.isFinite(value) ? value : 0);
            }, 0);
            return Math.max(maxValue, total);
        }, 0);
    });

    const chartPadding = $derived.by(() => {
        const label = Math.round(maxStackValue).toLocaleString();
        const estimatedLabelWidth = Math.max(48, Math.min(140, 12 + label.length * 8));
        return {
            top: 20,
            right: 12,
            bottom: 24,
            left: estimatedLabelWidth
        };
    });
</script>

{#if data.length > 0 && series.length > 0}
    <div class="metric-stacked-bar-chart__container">
        <div class="metric-stacked-bar-chart__scroll" bind:clientWidth={containerWidth}>
            <article class="metric-stacked-bar-chart" style={`width: ${chartWidth}px;`}>
                <BarChart
                    {data}
                    {series}
                    {bandPadding}
                    {x}
                    seriesLayout="stack"
                    padding={chartPadding}
                    props={{
                        bars: {
                            radius: 0
                        },
                        ...axisProps,
                        tooltip: {
                            root: {
                                classes: { root: 'layerchart-tooltip' }
                            }
                        }
                    }}
                />
            </article>
        </div>
        {#if showLegend}
            <ul class="metric-stacked-bar-chart__legend" aria-label="Chart legend">
                {#each series as item}
                    <li class="metric-stacked-bar-chart__legend-item">
                        <span
                            class="metric-stacked-bar-chart__legend-swatch"
                            style={`--legend-color: ${item.color ?? '#9aa0a6'}`}
                        ></span>
                        <span class="metric-stacked-bar-chart__legend-label">{item.label}</span>
                    </li>
                {/each}
            </ul>
        {/if}
    </div>
{/if}
