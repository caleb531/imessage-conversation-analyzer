<script lang="ts">
    import { invokeIcaCsv, MissingContactError, type IcaCsvHeader } from '$lib/cli';
    import { Grid, WillowDark } from '@svar-ui/svelte-grid';
    import {
        Button,
        DatePicker,
        DatePickerInput,
        InlineNotification,
        Loading,
        TooltipIcon
    } from 'carbon-components-svelte';
    import Information from 'carbon-icons-svelte/lib/Information.svelte';
    import { onMount, type Snippet } from 'svelte';
    import '../styles/result-grid.css';
    import type { GridColumn } from '../types';
    import DateCell from './DateCell.svelte';
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

    function createColumns(
        headers: IcaCsvHeader[],
        dataRows: Array<Record<string, unknown>>
    ): GridColumn[] {
        if (headers.length === 0) {
            return [];
        }
        const sample = dataRows[0] ?? {};
        return headers.map((header, index) => {
            const value = sample[header.id];
            const ValueFormatter = getValueFormatter(value as string | number);
            return {
                id: header.id,
                header: header.original,
                flexgrow: 1,
                width: 120,
                ...(ValueFormatter ? { cell: ValueFormatter } : {})
            } satisfies GridColumn;
        });
    }

    function padTimeUnit(value: number): string {
        return String(value).padStart(2, '0');
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
                                <span slot="labelText" class="result-grid__date-label">
                                    <span>From date</span>
                                    <TooltipIcon
                                        tooltipText="Starting from midnight on the specified start date"
                                    >
                                        <Information />
                                    </TooltipIcon>
                                </span>
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
                                <span slot="labelText" class="result-grid__date-label">
                                    <span>To date</span>
                                    <TooltipIcon
                                        tooltipText="Up to (but not including) the specified end date"
                                    >
                                        <Information />
                                    </TooltipIcon>
                                </span>
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
                title={`Unable to load ${title.toLowerCase()}`}
                subtitle={errorMessage}
            />
        {:else}
            <WillowDark>
                <Grid data={rows} {columns} />
            </WillowDark>
        {/if}
    {/if}
</section>
