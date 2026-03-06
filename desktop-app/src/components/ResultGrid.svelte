<script lang="ts">
    import { invokeIcaCsv, MissingContactError, type IcaCsvHeader } from '$lib/cli';
    import { buildDateFilterArgs, type DateFilterState } from '$lib/dateFilters';
    import { Grid, WillowDark } from '@svar-ui/svelte-grid';
    import { Button, Loading } from 'carbon-components-svelte';
    import { onMount, type Snippet } from 'svelte';
    import { SvelteMap } from 'svelte/reactivity';
    import '../styles/result-grid.css';
    import type { GridColumn } from '../types';
    import DateCell from './DateCell.svelte';
    import DateRangeFields from './DateRangeFields.svelte';
    import InlineNotification from './InlineNotification.svelte';
    import NumberCell from './NumberCell.svelte';

    // Props used by ResultGrid across all metric routes.
    interface Props {
        title: string;
        description: string;
        command: string[];
        charts?: Snippet<[Array<Record<string, unknown>>, GridColumn[]]>;
        chartsClass?: string;
        // Optional analyzer-specific controls rendered above date filters.
        parameters?: Snippet<[boolean]>;
        // Gates analysis execution until required analyzer inputs are present.
        isReady?: boolean;
        // User-facing explanation shown while analysis is gated by missing inputs.
        notReadyMessage?: string;
    }

    let {
        title,
        description,
        command,
        charts,
        chartsClass,
        parameters,
        isReady = true,
        notReadyMessage = ''
    }: Props = $props();

    // UI and data state for asynchronous loading lifecycle.
    let isReloadingData = $state(false);
    let hasInitiallyLoaded = $state(false);
    let errorMessage = $state('');
    let rows = $state<Array<Record<string, unknown>>>([]);
    let columns = $state<GridColumn[]>([]);

    // Controlled date picker values and currently applied filter snapshot.
    let fromDateInput = $state('');
    let toDateInput = $state('');
    // Forces date picker subtree recreation when clearing values.
    let datePickerResetKey = $state(0);
    let appliedFilters = $state<DateFilterState>({
        fromDate: '',
        toDate: ''
    });

    const FALLBACK_PIXELS_PER_CHAR = 10;
    const FALLBACK_FONT_WEIGHT = '400';
    const FALLBACK_FONT_SIZE = '16px';
    const FALLBACK_FONT_FAMILY = 'system-ui';
    const COLUMN_HORIZONTAL_PADDING_PX = 48;
    const MIN_COLUMN_WIDTH_PX = 120;
    const NUMBER_WIDTH_FORMATTER = new Intl.NumberFormat();
    const DATE_WIDTH_FORMATTER = new Intl.DateTimeFormat('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });

    let textMeasureContext: CanvasRenderingContext2D | null = null;
    let textMeasureFont = '';
    const textWidthCache = new SvelteMap<string, number>();

    const cellFormatters = [
        {
            pattern: /^\d+$/,
            component: NumberCell
        },
        {
            pattern: /^\d{4}-\d{2}-\d{2}$/,
            component: DateCell
        }
    ];

    function getValueFormatter(value: string | number) {
        for (const formatter of cellFormatters) {
            if (formatter.pattern.test(String(value))) {
                return formatter.component;
            }
        }
        return null;
    }

    function formatCellValueForWidth(value: unknown): string {
        // Mirror display formatting so measured width matches what users actually see.
        if (value === null || value === undefined) {
            return '';
        }

        const stringValue = String(value);
        if (/^\d+$/.test(stringValue)) {
            return NUMBER_WIDTH_FORMATTER.format(Number(stringValue));
        }
        if (/^\d{4}-\d{2}-\d{2}$/.test(stringValue)) {
            return DATE_WIDTH_FORMATTER.format(new Date(stringValue));
        }
        return stringValue;
    }

    function getMeasurementContext(): CanvasRenderingContext2D | null {
        if (textMeasureContext) {
            return textMeasureContext;
        }

        if (typeof window === 'undefined' || typeof document === 'undefined') {
            return null;
        }

        const canvas = document.createElement('canvas');
        textMeasureContext = canvas.getContext('2d');
        return textMeasureContext;
    }

    function getMeasurementFont(): string {
        if (typeof window === 'undefined' || typeof document === 'undefined') {
            return `${FALLBACK_FONT_WEIGHT} ${FALLBACK_FONT_SIZE} ${FALLBACK_FONT_FAMILY}`;
        }

        const bodyStyles = getComputedStyle(document.body);
        const fontWeight = bodyStyles.fontWeight || FALLBACK_FONT_WEIGHT;
        const fontSize = bodyStyles.fontSize || FALLBACK_FONT_SIZE;
        const fontFamily = bodyStyles.fontFamily || FALLBACK_FONT_FAMILY;
        return `${fontWeight} ${fontSize} ${fontFamily}`;
    }

    function measureTextWidthPx(text: string): number {
        // Measure in pixels using current document font; fallback keeps SSR/edge cases safe.
        if (typeof window === 'undefined' || typeof document === 'undefined') {
            // Server-side/no-DOM fallback: approximate width from character count.
            return text.length * FALLBACK_PIXELS_PER_CHAR;
        }

        const context = getMeasurementContext();
        if (!context) {
            // If canvas context is unavailable, keep the same deterministic fallback.
            return text.length * FALLBACK_PIXELS_PER_CHAR;
        }

        const font = getMeasurementFont();
        if (textMeasureFont !== font) {
            // Font changes affect text metrics, so resync context and invalidate cached widths.
            textMeasureFont = font;
            context.font = font;
            textWidthCache.clear();
        }

        const cached = textWidthCache.get(text);
        if (cached !== undefined) {
            // Hot path: repeated values (common in tables) skip re-measurement.
            return cached;
        }

        const measuredWidth = Math.ceil(context.measureText(text).width);
        textWidthCache.set(text, measuredWidth);

        return measuredWidth;
    }

    function computeColumnWidth(
        header: IcaCsvHeader,
        dataRows: Array<Record<string, unknown>>
    ): number {
        // Ensure each column can fit both header and widest formatted cell value.
        let widest = measureTextWidthPx(header.original);

        for (const row of dataRows) {
            const text = formatCellValueForWidth(row[header.id]);
            widest = Math.max(widest, measureTextWidthPx(text));
        }

        // Include cell padding/sort affordance breathing room to avoid clipped text.
        return Math.max(MIN_COLUMN_WIDTH_PX, widest + COLUMN_HORIZONTAL_PADDING_PX);
    }

    function createColumns(
        headers: IcaCsvHeader[],
        dataRows: Array<Record<string, unknown>>
    ): GridColumn[] {
        if (headers.length === 0) {
            return [];
        }
        const sample = dataRows[0] ?? {};
        return headers.map((header) => {
            const value = sample[header.id];
            const ValueFormatter = getValueFormatter(value as string | number);
            return {
                id: header.id,
                header: header.original,
                width: computeColumnWidth(header, dataRows),
                ...(ValueFormatter ? { cell: ValueFormatter } : {})
            } satisfies GridColumn;
        });
    }

    // Loads grid data from ICA using any currently applied date filters.
    async function loadData(filters: DateFilterState = appliedFilters) {
        if (!isReady) {
            return;
        }
        isReloadingData = true;
        errorMessage = '';
        try {
            const filterArgs = buildDateFilterArgs(filters);
            const result = await invokeIcaCsv([...command, ...filterArgs]);
            rows = result.rows;
            columns = createColumns(result.headers, result.rows);
        } catch (error) {
            if (error instanceof MissingContactError) {
                errorMessage = error.message;
            } else {
                errorMessage = error instanceof Error ? error.message : String(error);
            }
        } finally {
            isReloadingData = false;
            hasInitiallyLoaded = true;
        }
    }

    // Applies in-progress date input values as the next active filter set.
    function applyFilters() {
        if (!isReady) {
            return;
        }
        const nextFilters: DateFilterState = {
            fromDate: fromDateInput,
            toDate: toDateInput
        };
        appliedFilters = nextFilters;
        void loadData(nextFilters);
    }

    // Handles form submit so Apply triggers filtered data reload.
    function submitFilters(event: Event) {
        event.preventDefault();
        applyFilters();
    }

    // Handles form reset so Clear runs custom reset behavior.
    function resetFilters(event: Event) {
        event.preventDefault();
        clearFilters();
    }

    // Resets date filters to empty and reloads unfiltered results.
    function clearFilters() {
        fromDateInput = '';
        toDateInput = '';
        datePickerResetKey += 1;
        const cleared: DateFilterState = {
            fromDate: '',
            toDate: ''
        };
        appliedFilters = cleared;
        if (isReady) {
            void loadData(cleared);
        }
    }

    // Initial data fetch when the grid first mounts.
    onMount(() => {
        if (isReady) {
            void loadData();
            return;
        }

        hasInitiallyLoaded = true;
    });
</script>

<section class="result-grid">
    <header>
        <h2>{title}</h2>
        <p>{description}</p>
    </header>

    {#if isReloadingData && !hasInitiallyLoaded}
        <div class="result-grid__loading">
            <Loading withOverlay={false} />
        </div>
    {:else}
        <form
            class="result-grid__filters"
            aria-label="Analyzer filters"
            onsubmit={submitFilters}
            onreset={resetFilters}
        >
            {#snippet actionButtons()}
                <div class="result-grid__filters-actions">
                    {#if isReloadingData && hasInitiallyLoaded}
                        <div class="result-grid__soft-loading" aria-live="polite">
                            <Loading withOverlay={false} small />
                        </div>
                    {/if}
                    <Button
                        kind="primary"
                        size="small"
                        type="submit"
                        disabled={isReloadingData || !isReady}
                    >
                        {isReloadingData ? 'Loading...' : 'Apply'}
                    </Button>
                    <Button kind="secondary" size="small" type="reset" disabled={isReloadingData}>
                        Clear
                    </Button>
                </div>
            {/snippet}

            {#if parameters}
                <div class="result-grid__filters-row result-grid__filters-row--parameters">
                    {@render parameters(isReloadingData)}
                </div>
            {/if}

            <div class="result-grid__filters-row result-grid__filters-row--main">
                {#key datePickerResetKey}
                    <DateRangeFields
                        fromDateInputId="result-grid-from-date"
                        toDateInputId="result-grid-to-date"
                        bind:fromDate={fromDateInput}
                        bind:toDate={toDateInput}
                        disabled={isReloadingData}
                    />
                {/key}
                {#if !parameters}
                    {@render actionButtons()}
                {/if}
            </div>

            {#if parameters}
                <div class="result-grid__filters-row result-grid__filters-row--actions">
                    {@render actionButtons()}
                </div>
            {/if}
        </form>

        {#if charts && rows.length && !errorMessage}
            <div
                class={`result-grid-charts${chartsClass ? ` ${chartsClass}` : ''}`}
                aria-label="Chart area"
                role="img"
            >
                {@render charts(rows, columns)}
            </div>
        {/if}

        {#if !isReady && notReadyMessage}
            <InlineNotification
                class="result-grid__error"
                kind="info"
                title="Waiting for input"
                subtitle={notReadyMessage}
            />
        {:else if errorMessage}
            <InlineNotification
                class="result-grid__error"
                kind="error"
                title="Error"
                subtitle={errorMessage}
            />
        {:else}
            <article class="result-grid__grid-container">
                <WillowDark>
                    <Grid data={rows} {columns} />
                </WillowDark>
            </article>
        {/if}
    {/if}
</section>
