<script lang="ts">
    import { invokeIcaCsv, MissingContactError, type IcaCsvHeader } from '$lib/cli';
    import { Grid, WillowDark } from '@svar-ui/svelte-grid';
    import {
        Button,
        DatePicker,
        DatePickerInput,
        Loading,
        TooltipIcon
    } from 'carbon-components-svelte';
    import Information from 'carbon-icons-svelte/lib/Information.svelte';
    import { onMount, type Snippet } from 'svelte';
    import { SvelteMap } from 'svelte/reactivity';
    import '../styles/result-grid.css';
    import type { GridColumn } from '../types';
    import DateCell from './DateCell.svelte';
    import InlineNotification from './InlineNotification.svelte';
    import NumberCell from './NumberCell.svelte';

    interface Props {
        title: string;
        description: string;
        command: string[];
        charts?: Snippet<[Array<Record<string, unknown>>, GridColumn[]]>;
        children?: Snippet;
        chartsClass?: string;
    }

    let { title, description, command, charts, children, chartsClass }: Props = $props();

    let isReloadingData = $state(true);
    let hasInitiallyLoaded = $state(false);
    let errorMessage = $state('');
    let rows = $state<Array<Record<string, unknown>>>([]);
    let columns = $state<GridColumn[]>([]);

    type DateFilterState = {
        fromDate: string;
        toDate: string;
    };

    let fromDateInput = $state('');
    let toDateInput = $state('');
    let datePickerResetKey = $state(0);
    let appliedFilters = $state<DateFilterState>({
        fromDate: '',
        toDate: ''
    });

    const TIME_UNIT_PAD_LENGTH = 2;
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

    function padTimeUnit(value: number): string {
        return String(value).padStart(TIME_UNIT_PAD_LENGTH, '0');
    }

    function normalizeDateInput(value: string): string | null {
        const trimmed = value.trim();
        if (!trimmed) return null;
        const isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trimmed);
        if (isoMatch) return trimmed;
        const slashMatch = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(trimmed);
        if (slashMatch) {
            const month = padTimeUnit(Number(slashMatch[1]));
            const day = padTimeUnit(Number(slashMatch[2]));
            return `${slashMatch[3]}-${month}-${day}`;
        }
        return null;
    }

    function buildDateValue(dateValue: string): string | null {
        return normalizeDateInput(dateValue);
    }

    function buildFilterArgs(filters: DateFilterState): string[] {
        const args: string[] = [];
        const fromValue = buildDateValue(filters.fromDate);
        const toValue = buildDateValue(filters.toDate);
        if (fromValue) {
            args.push('--from-date', fromValue);
        }
        if (toValue) {
            args.push('--to-date', toValue);
        }
        return args;
    }

    async function loadData(filters: DateFilterState = appliedFilters) {
        isReloadingData = true;
        errorMessage = '';
        try {
            const filterArgs = buildFilterArgs(filters);
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

    function applyFilters() {
        const nextFilters: DateFilterState = {
            fromDate: fromDateInput,
            toDate: toDateInput
        };
        appliedFilters = nextFilters;
        void loadData(nextFilters);
    }

    function submitFilters(event: Event) {
        event.preventDefault();
        applyFilters();
    }

    function resetFilters(event: Event) {
        event.preventDefault();
        clearFilters();
    }

    function clearFilters() {
        fromDateInput = '';
        toDateInput = '';
        datePickerResetKey += 1;
        const cleared: DateFilterState = {
            fromDate: '',
            toDate: ''
        };
        appliedFilters = cleared;
        void loadData(cleared);
    }

    onMount(() => {
        void loadData();
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
            aria-label="Date filters"
            onsubmit={submitFilters}
            onreset={resetFilters}
        >
            <div class="result-grid__filters-row result-grid__filters-row--main">
                {#key datePickerResetKey}
                    <div class="result-grid__filters-fields">
                        <DatePicker
                            datePickerType="single"
                            dateFormat="m/d/Y"
                            bind:value={fromDateInput}
                        >
                            <DatePickerInput
                                id="result-grid-from-date"
                                size="sm"
                                labelText="From date"
                                placeholder="mm/dd/yyyy"
                            >
                                {#snippet labelChildren()}
                                    <span class="result-grid__date-label">
                                        <span>From date</span>
                                        <TooltipIcon
                                            tooltipText="Starting from midnight on the specified start date"
                                        >
                                            <Information />
                                        </TooltipIcon>
                                    </span>
                                {/snippet}
                            </DatePickerInput>
                        </DatePicker>
                        <DatePicker
                            datePickerType="single"
                            dateFormat="m/d/Y"
                            bind:value={toDateInput}
                        >
                            <DatePickerInput
                                id="result-grid-to-date"
                                size="sm"
                                labelText="To date"
                                placeholder="mm/dd/yyyy"
                            >
                                {#snippet labelChildren()}
                                    <span class="result-grid__date-label">
                                        <span>To date</span>
                                        <TooltipIcon
                                            tooltipText="Up to (but not including) the specified end date"
                                        >
                                            <Information />
                                        </TooltipIcon>
                                    </span>
                                {/snippet}
                            </DatePickerInput>
                        </DatePicker>
                    </div>
                {/key}
                <div class="result-grid__filters-actions">
                    {#if isReloadingData && hasInitiallyLoaded}
                        <div class="result-grid__soft-loading" aria-live="polite">
                            <Loading withOverlay={false} small />
                        </div>
                    {/if}
                    <Button kind="primary" size="small" type="submit" disabled={isReloadingData}>
                        {isReloadingData ? 'Loading...' : 'Apply'}
                    </Button>
                    <Button kind="secondary" size="small" type="reset" disabled={isReloadingData}>
                        Clear
                    </Button>
                </div>
            </div>
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

        {#if errorMessage}
            <InlineNotification
                class="result-grid__error"
                kind="error"
                title="Error"
                subtitle={errorMessage}
            />
        {:else}
            <WillowDark>
                <Grid data={rows} {columns} />
            </WillowDark>
        {/if}
    {/if}
</section>
