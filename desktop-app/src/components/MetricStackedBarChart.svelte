<script lang="ts">
    import { BarChart } from 'layerchart';
    import '../styles/metric-stacked-bar-chart.css';

    // Generic datum shape consumed by LayerChart stacked series.
    type StackedDatum = Record<string, string | number>;
    // Series metadata used to define stacked bars and legend entries.
    type StackedSeries = { key: string; label: string; color?: string };
    // Optional grouped x-axis labels rendered beneath the primary axis.
    type GroupLabel = { label: string; startIndex: number };
    // Tick label formatter used by axis configuration.
    type TickFormatter = (_value: string | number) => string;

    // Public props for chart data, orientation, and rendering options.
    let {
        data,
        series,
        x = 'key',
        orientation = 'vertical',
        bandPadding = 0.2,
        labelType = 'string',
        showAllCategoryLabels = false,
        minLabelWidth = 90,
        barWidth = 6,
        showLegend = true,
        xGroupLabels = [],
        xTickFormat
    }: {
        data: StackedDatum[];
        series: StackedSeries[];
        x?: string;
        orientation?: 'vertical' | 'horizontal';
        bandPadding?: number;
        labelType?: 'string' | 'emoji';
        showAllCategoryLabels?: boolean;
        minLabelWidth?: number;
        barWidth?: number;
        showLegend?: boolean;
        xGroupLabels?: GroupLabel[];
        xTickFormat?: TickFormatter;
    } = $props();

    // Measured width of the scroll container used for responsive tick density.
    let containerWidth = $state(0);

    // CSS class applied to x-axis labels based on label type.
    const labelClass = $derived(labelType === 'emoji' ? 'emoji-tick-label' : 'text-tick-label');
    // Derived orientation flag used to branch chart configuration.
    const isHorizontal = $derived(orientation === 'horizontal');

    // Category values extracted from input rows for axis tick generation.
    const categoryValues = $derived.by(() =>
        data
            .map((datum) => datum[x])
            .filter((value): value is string | number => value !== null && value !== undefined)
    );

    // Full-category tick list used when every category should be shown.
    const categoryTicks = $derived.by(() =>
        showAllCategoryLabels && categoryValues.length > 0 ? categoryValues : undefined
    );

    // X-axis field assignment for vertical charts.
    const chartX = $derived(isHorizontal ? undefined : x);
    // Y-axis field assignment for horizontal charts.
    const chartY = $derived(isHorizontal ? x : undefined);

    // Dynamic fallback tick count based on available container width.
    const tickCount = $derived.by(() => {
        if (containerWidth <= 0) {
            return 4;
        }
        return Math.max(2, Math.floor(containerWidth / minLabelWidth));
    });

    // Effective chart width used to preserve readable bar widths for dense datasets.
    const chartWidth = $derived.by(() => {
        if (isHorizontal) {
            return containerWidth;
        }
        if (data.length === 0) {
            return containerWidth;
        }
        return Math.max(containerWidth, data.length * barWidth);
    });

    // Axis configuration object switched by orientation.
    const axisProps = $derived.by(() =>
        isHorizontal
            ? {
                  xAxis: {
                      ticks: 5
                  },
                  yAxis: {
                      ...(categoryTicks ? { ticks: categoryTicks } : {}),
                      ...(xTickFormat ? { format: xTickFormat } : {}),
                      tickLabelProps: {
                          class: labelClass
                      }
                  }
              }
            : {
                  xAxis: {
                      ticks: categoryTicks ?? tickCount,
                      ...(xTickFormat ? { format: xTickFormat } : {}),
                      tickLabelProps: {
                          class: labelClass
                      }
                  },
                  yAxis: {
                      ticks: 5
                  }
              }
    );

    // Show only the requested axis gridlines by orientation.
    const gridProps = $derived(
        isHorizontal
            ? {
                  x: {
                      class: 'metric-stacked-bar-chart__gridline'
                  },
                  y: false
              }
            : {
                  x: false,
                  y: {
                      class: 'metric-stacked-bar-chart__gridline'
                  }
              }
    );

    // Resolves CSS variable colors into concrete values for legend/chart consistency.
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

    // Series list with resolved fallback colors.
    const chartSeries = $derived.by(() =>
        series.map((item) => ({
            ...item,
            color: resolveColor(item.color ?? 'var(--color-chart-legend-fallback)')
        }))
    );

    // Maximum stacked total used to size chart paddings and axis label room.
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

    // Responsive chart padding tuned for horizontal vs vertical layouts.
    const chartPadding = $derived.by(() => {
        if (isHorizontal) {
            const widestLabel = categoryValues.reduce<number>((maxWidth, value) => {
                const label = xTickFormat ? xTickFormat(value) : String(value ?? '');
                return Math.max(maxWidth, estimateTickLabelWidth(label));
            }, 0);
            const maxValueLabel = Math.round(maxStackValue).toLocaleString();
            const maxValueLabelWidth = estimateTickLabelWidth(maxValueLabel);
            return {
                top: 20,
                right: Math.max(20, Math.ceil(maxValueLabelWidth / 2) + 10),
                bottom: 24,
                left: Math.max(72, Math.min(260, widestLabel + 16))
            };
        }

        const label = Math.round(maxStackValue).toLocaleString();
        const estimatedLabelWidth = Math.max(48, Math.min(140, 12 + label.length * 8));
        return {
            top: 20,
            right: 12,
            bottom: 24,
            left: estimatedLabelWidth
        };
    });

    // Approximates rendered tick label width for axis/padding calculations.
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

        context.font =
            '16px -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif';
        return context.measureText(compactLabel).width;
    }

    // Computes pixel positions for optional year/group sub-axis labels.
    const groupLabelPositions = $derived.by(() => {
        if (isHorizontal || xGroupLabels.length === 0 || data.length === 0) {
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
                        chartPadding.left +
                        outerPadding * step +
                        group.startIndex * step +
                        bandwidth / 2;
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
                        x={chartX}
                        y={chartY}
                        {orientation}
                        series={chartSeries}
                        {bandPadding}
                        grid={gridProps}
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
