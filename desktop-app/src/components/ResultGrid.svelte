<script lang="ts">
    import { invokeIcaCsv, MissingContactError, type IcaCsvHeader } from '$lib/cli';
    import { buildDateFilterArgs, type DateFilterState } from '$lib/dateFilters';
    import { Grid, WillowDark } from '@svar-ui/svelte-grid';
    import { Button, Loading } from 'carbon-components-svelte';
    import { onMount, untrack, type Snippet } from 'svelte';
    import { SvelteMap } from 'svelte/reactivity';
    import '../styles/result-grid.css';
    import type { GridColumn } from '../types';
    import DateCell from './DateCell.svelte';
    import DateRangeFields from './DateRangeFields.svelte';
    import InlineNotification from './InlineNotification.svelte';
    import NumberCell from './NumberCell.svelte';

    // Props used by ResultGrid across all metric routes.
    interface Props {
        command: string[];
        charts?: Snippet<[Array<Record<string, unknown>>, GridColumn[]]>;
        chartsClass?: string;
        // Controls chart+grid placement: vertical stacks, horizontal places them side-by-side.
        layout?: 'vertical' | 'horizontal';
        // Controls chart area arrangement when more than one chart is rendered.
        chartLayout?: 'vertical' | 'horizontal';
        // Optional analyzer-specific controls rendered above date filters.
        parameters?: Snippet<[boolean]>;
        // Gates analysis execution until required analyzer inputs are present.
        isReady?: boolean;
        // User-facing explanation shown while analysis is gated by missing inputs.
        notReadyMessage?: string;
        // Stable key that isolates persisted date-filter values for this specific ResultGrid.
        dateFilterPersistenceKey?: string;
        // Prefix used to keep date input element IDs unique on pages with multiple ResultGrid instances.
        dateInputIdPrefix?: string;
    }

    let {
        command,
        charts,
        chartsClass,
        layout = 'vertical',
        chartLayout = 'horizontal',
        parameters,
        isReady = true,
        notReadyMessage = '',
        dateFilterPersistenceKey,
        dateInputIdPrefix
    }: Props = $props();

    // Generates stable date input IDs and avoids collisions when multiple grids render on one page.
    function buildDateInputId(field: 'from' | 'to'): string {
        const prefixCandidate = dateInputIdPrefix?.trim() || dateFilterPersistenceKey?.trim();
        return `${prefixCandidate ?? 'result-grid'}-${field}-date`;
    }

    // UI and data state for asynchronous loading lifecycle.
    let isReloadingData = $state(false);
    let hasInitiallyLoaded = $state(false);
    let errorMessage = $state('');
    let rows = $state<Array<Record<string, unknown>>>([]);
    let columns = $state<GridColumn[]>([]);

    // Controlled date picker values and currently applied filter snapshot.
    let fromDateInput = $state('');
    let toDateInput = $state('');
    // Mirrors DateRangeFields persistence readiness so first load can wait for hydrated values.
    let hasLoadedPersistedDateFilters = $state(false);
    // Holds non-blocking persistence errors shown below filter controls.
    let dateFilterPersistenceError = $state('');
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

    let previousCommandStr = $state('');
    let currentLoadId = $state(0);

    // Loads grid data from ICA using any currently applied date filters.
    async function loadData(filters: DateFilterState = appliedFilters) {
        if (!isReady) {
            return;
        }

        currentLoadId += 1;
        const loadId = currentLoadId;

        isReloadingData = true;
        errorMessage = '';
        try {
            const filterArgs = buildDateFilterArgs(filters);
            const result = await invokeIcaCsv([...command, ...filterArgs]);

            if (loadId !== currentLoadId) return;

            rows = result.rows;
            columns = createColumns(result.headers, result.rows);
        } catch (error) {
            if (loadId !== currentLoadId) return;

            if (error instanceof MissingContactError) {
                errorMessage = error.message;
            } else {
                errorMessage = error instanceof Error ? error.message : String(error);
            }
        } finally {
            if (loadId === currentLoadId) {
                isReloadingData = false;
                hasInitiallyLoaded = true;
            }
        }
    }

    $effect(() => {
        if (!hasInitiallyLoaded || !hasLoadedPersistedDateFilters) {
            previousCommandStr = JSON.stringify(command);
            return;
        }

        const currentCommandStr = JSON.stringify(command);
        const currentFrom = fromDateInput;
        const currentTo = toDateInput;
        const currentReady = isReady;

        untrack(() => {
            let shouldLoad = false;

            if (currentCommandStr !== previousCommandStr) {
                previousCommandStr = currentCommandStr;
                shouldLoad = true;
            }

            if (currentFrom !== appliedFilters.fromDate || currentTo !== appliedFilters.toDate) {
                appliedFilters = { fromDate: currentFrom, toDate: currentTo };
                shouldLoad = true;
            }

            if (shouldLoad && currentReady) {
                void loadData(appliedFilters);
            }
        });
    });

    // Performs the first data load only after DateRangeFields has finished hydrating persisted values.
    $effect(() => {
        if (hasInitiallyLoaded || !hasLoadedPersistedDateFilters) {
            return;
        }

        const currentFrom = fromDateInput;
        const currentTo = toDateInput;
        const currentReady = isReady;

        untrack(() => {
            appliedFilters = { fromDate: currentFrom, toDate: currentTo };

            if (currentReady) {
                void loadData(appliedFilters);
                return;
            }

            hasInitiallyLoaded = true;
        });
    });

    // Handles form reset so Clear runs custom reset behavior.
    function resetFilters(event: Event) {
        event.preventDefault();
        clearFilters();
    }

    // Resets date inputs. The `$effect` observer will automatically reload the grid.
    function clearFilters() {
        fromDateInput = '';
        toDateInput = '';
        datePickerResetKey += 1;
    }

    // Initializes command tracking; first data load is handled by a readiness-aware effect.
    onMount(() => {
        previousCommandStr = JSON.stringify(command);
    });
</script>

<article class="result-grid">
    {#if isReloadingData && !hasInitiallyLoaded}
        <div class="result-grid__loading">
            <Loading withOverlay={false} />
        </div>
    {:else}
        <form class="result-grid__filters" aria-label="Analyzer filters" onreset={resetFilters}>
            {#if parameters}
                <div class="result-grid__filters-row result-grid__filters-row--parameters">
                    {@render parameters(isReloadingData)}
                </div>
            {/if}

            <div class="result-grid__filters-row result-grid__filters-row--main">
                {#key datePickerResetKey}
                    <DateRangeFields
                        fromDateInputId={buildDateInputId('from')}
                        toDateInputId={buildDateInputId('to')}
                        {dateFilterPersistenceKey}
                        bind:persistenceError={dateFilterPersistenceError}
                        bind:hasLoadedPersistedDateFilters
                        bind:fromDate={fromDateInput}
                        bind:toDate={toDateInput}
                    />
                {/key}
                <div class="result-grid__filters-actions">
                    {#if isReloadingData && hasInitiallyLoaded}
                        <div class="result-grid__soft-loading" aria-live="polite">
                            <Loading withOverlay={false} small />
                        </div>
                    {/if}
                    <Button kind="secondary" size="small" type="reset">Clear</Button>
                </div>
            </div>

            {#if dateFilterPersistenceError}
                <InlineNotification
                    class="result-grid__error"
                    kind="error"
                    title="Error"
                    subtitle={`Failed to save date filters: ${dateFilterPersistenceError}`}
                />
            {/if}
        </form>

        <div class={`result-grid__content result-grid__content--${layout}`}>
            {#if charts && rows.length && !errorMessage}
                <div
                    class={`result-grid-charts result-grid-charts--${chartLayout}${chartsClass ? ` ${chartsClass}` : ''}`}
                    aria-label="Chart area"
                    role="img"
                >
                    {@render charts(rows, columns)}
                </div>
            {/if}

            <section class="result-grid__grid-region">
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
            </section>
        </div>
    {/if}
</article>
