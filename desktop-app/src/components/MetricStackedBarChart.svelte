<script lang="ts">
    import { BarChart } from 'layerchart';
    import '../styles/metric-stacked-bar-chart.css';

    type StackedDatum = Record<string, string | number>;
    type StackedSeries = { key: string; label: string; color?: string };
    type GroupLabel = { label: string; startIndex: number };
    type TickFormatter = (value: string | number) => string;

    let {
        data,
        series,
        x = 'key',
        bandPadding = 0.2,
        labelType = 'string',
        minLabelWidth = 90,
        barWidth = 6,
        showLegend = true,
        xGroupLabels = [],
        xTickFormat
    }: {
        data: StackedDatum[];
        series: StackedSeries[];
        x?: string;
        bandPadding?: number;
        labelType?: 'string' | 'emoji';
        minLabelWidth?: number;
        barWidth?: number;
        showLegend?: boolean;
        xGroupLabels?: GroupLabel[];
        xTickFormat?: TickFormatter;
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
            ...(xTickFormat ? { format: xTickFormat } : {}),
            tickLabelProps: {
                class: labelClass
            }
        },
        yAxis: {
            ticks: 5
        }
    }));

    function resolveColor(color: string): string {
        if (typeof window === 'undefined') {
            return color;
        }

        const match = color.match(/^var\((--[^),\s]+)(?:,\s*[^)]+)?\)$/);
        if (!match) {
            return color;
        }

        const resolved = getComputedStyle(document.documentElement)
            .getPropertyValue(match[1])
            .trim();
        return resolved || color;
    }

    const chartSeries = $derived.by(() =>
        series.map((item) => ({
            ...item,
            color: resolveColor(item.color ?? 'var(--color-chart-legend-fallback)')
        }))
    );

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

    function estimateTickLabelWidth(label: string): number {
        const compactLabel = label.trim();
        if (!compactLabel) {
            return 0;
        }

        if (typeof document === 'undefined') {
            return compactLabel.length * 8;
        }

        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        if (!context) {
            return compactLabel.length * 8;
        }

        context.font = '16px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif';
        return context.measureText(compactLabel).width;
    }

    const groupLabelPositions = $derived.by(() => {
        if (xGroupLabels.length === 0 || data.length === 0) {
            return [];
        }

        const chartAreaWidth = Math.max(0, chartWidth - chartPadding.left - chartPadding.right);
        if (chartAreaWidth === 0) {
            return [];
        }

        const innerPadding = Math.max(0, Math.min(0.95, bandPadding));
        const outerPadding = innerPadding;
        const step = chartAreaWidth / Math.max(1, data.length - innerPadding + outerPadding * 2);
        const bandwidth = step * (1 - innerPadding);

        return xGroupLabels
            .filter((group) => group.startIndex >= 0 && group.startIndex < data.length)
            .map((group) => ({
                ...group,
                left: (() => {
                    const datum = data[group.startIndex];
                    const xValue = datum?.[x] ?? '';
                    const tickLabel = xTickFormat ? xTickFormat(xValue) : String(xValue ?? '');
                    const tickLabelWidth = estimateTickLabelWidth(tickLabel);
                    const tickCenter =
                        chartPadding.left + outerPadding * step + group.startIndex * step + bandwidth / 2;
                    return tickCenter - tickLabelWidth / 2;
                })()
            }));
    });
</script>

{#if data.length > 0 && series.length > 0}
    <div class="metric-stacked-bar-chart__container">
        <div class="metric-stacked-bar-chart__scroll" bind:clientWidth={containerWidth}>
            <div class="metric-stacked-bar-chart__inner" style={`width: ${chartWidth}px;`}>
                <article class="metric-stacked-bar-chart">
                    <BarChart
                        {data}
                        series={chartSeries}
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
                {#if groupLabelPositions.length > 0}
                    <div class="metric-stacked-bar-chart__subaxis" aria-hidden="true">
                        {#each groupLabelPositions as group (`${group.label}-${group.startIndex}`)}
                            <span
                                class="metric-stacked-bar-chart__subaxis-label"
                                style={`left: ${group.left}px;`}>{group.label}</span
                            >
                        {/each}
                    </div>
                {/if}
            </div>
        </div>
        {#if showLegend}
            <ul class="metric-stacked-bar-chart__legend" aria-label="Chart legend">
                <!-- eslint-disable-next-line svelte/require-each-key -->
                {#each series as item}
                    <li class="metric-stacked-bar-chart__legend-item">
                        <span
                            class="metric-stacked-bar-chart__legend-swatch"
                            style={`--legend-color: ${item.color ?? 'var(--color-chart-legend-fallback)'}`}
                        ></span>
                        <span class="metric-stacked-bar-chart__legend-label">{item.label}</span>
                    </li>
                {/each}
            </ul>
        {/if}
    </div>
{/if}
