<script lang="ts">
    import { BarChart } from 'layerchart';
    import '../styles/metric-bar-chart.css';
    import type { DataPoint } from '../types';

    let {
        data,
        x = 'key',
        y = 'value',
        orientation = 'vertical',
        labelType = 'string'
    }: {
        data: DataPoint[];
        x?: string;
        y?: string;
        color?: string;
        orientation?: 'vertical' | 'horizontal';
        labelType?: 'string' | 'emoji';
    } = $props();

    const chartX = $derived(orientation === 'horizontal' ? y : x);
    const chartY = $derived(orientation === 'horizontal' ? x : y);
    const labelClass = $derived(labelType === 'emoji' ? 'emoji-tick-label' : 'text-tick-label');
    let barColor = $state('var(--color-chart-series-1)');

    const axisProps = $derived(
        orientation === 'horizontal'
            ? {
                  xAxis: {
                      ticks: 5
                  },
                  yAxis: {
                      tickLabelProps: {
                          class: labelClass
                      }
                  }
              }
            : {
                  xAxis: {
                      tickLabelProps: {
                          class: labelClass
                      }
                  },
                  yAxis: {
                      ticks: 5
                  }
              }
    );
</script>

{#if data.length > 0}
    <article class="metric-bar-chart">
        <BarChart
            {data}
            x={chartX}
            y={chartY}
            {orientation}
            bandPadding={0.3}
            props={{
                bars: {
                    radius: 4,
                    fill: barColor
                },
                ...axisProps,
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
