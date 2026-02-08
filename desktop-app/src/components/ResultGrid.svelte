<script lang="ts">
    import { invokeIcaCsv, MissingContactError, type IcaCsvHeader } from '$lib/cli';
    import { Grid, WillowDark } from '@svar-ui/svelte-grid';
    import {
        Button,
        DatePicker,
        DatePickerInput,
        InlineNotification,
        Loading,
        TimePicker,
        Toggle
    } from 'carbon-components-svelte';
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
    }

    let { title, description, command, charts, children }: Props = $props();

    let isReloadingData = $state(true);
    let hasInitiallyLoaded = $state(false);
    let errorMessage = $state('');
    let rows = $state<Array<Record<string, unknown>>>([]);
    let columns = $state<GridColumn[]>([]);

    type DateFilterState = {
        fromDate: string;
        toDate: string;
        fromTime: string;
        toTime: string;
        enableTime: boolean;
    };

    let fromDateInput = $state('');
    let toDateInput = $state('');
    let fromTimeInput = $state('');
    let toTimeInput = $state('');
    let enableTimeInput = $state(false);
    let appliedFilters = $state<DateFilterState>({
        fromDate: '',
        toDate: '',
        fromTime: '',
        toTime: '',
        enableTime: false
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

    function readInputValue(event: Event): string {
        const target = event.target as HTMLInputElement | null;
        return target?.value ?? '';
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

    function normalizeTimeInput(value: string): string | null {
        const trimmed = value.trim();
        if (!trimmed) return null;
        const match = /^(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(trimmed);
        if (!match) return null;
        const hours = Number(match[1]);
        const minutes = Number(match[2]);
        const seconds = match[3] ? Number(match[3]) : 0;
        if (Number.isNaN(hours) || Number.isNaN(minutes) || Number.isNaN(seconds)) {
            return null;
        }
        if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59 || seconds < 0 || seconds > 59) {
            return null;
        }
        return `${padTimeUnit(hours)}:${padTimeUnit(minutes)}:${padTimeUnit(seconds)}`;
    }

    function buildDateValue(
        dateValue: string,
        timeValue: string,
        includeTime: boolean
    ): string | null {
        const normalizedDate = normalizeDateInput(dateValue);
        if (!normalizedDate) return null;
        if (!includeTime) return normalizedDate;
        const normalizedTime = normalizeTimeInput(timeValue);
        if (!normalizedTime) return normalizedDate;
        return `${normalizedDate}T${normalizedTime}`;
    }

    function buildFilterArgs(filters: DateFilterState): string[] {
        const args: string[] = [];
        const fromValue = buildDateValue(filters.fromDate, filters.fromTime, filters.enableTime);
        const toValue = buildDateValue(filters.toDate, filters.toTime, filters.enableTime);
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
            toDate: toDateInput,
            fromTime: fromTimeInput,
            toTime: toTimeInput,
            enableTime: enableTimeInput
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
        fromTimeInput = '';
        toTimeInput = '';
        enableTimeInput = false;
        const cleared: DateFilterState = {
            fromDate: '',
            toDate: '',
            fromTime: '',
            toTime: '',
            enableTime: false
        };
        appliedFilters = cleared;
        void loadData(cleared);
    }

    function handleTimeToggle(event: CustomEvent<{ toggled: boolean }>) {
        enableTimeInput = event.detail.toggled;
        if (!enableTimeInput) {
            fromTimeInput = '';
            toTimeInput = '';
        }
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
        {#if charts && rows.length && !errorMessage}
            <div class="result-grid-charts" aria-label="Chart area" role="img">
                {@render charts(rows, columns)}
            </div>
        {/if}

        <form
            class="result-grid__filters"
            class:result-grid__filters--with-time={enableTimeInput}
            aria-label="Date filters"
            onsubmit={submitFilters}
            onreset={resetFilters}
        >
            <div class="result-grid__filters-row">
                <Toggle
                    labelText="Include time"
                    labelA="Date only"
                    labelB="Date + time"
                    toggled={enableTimeInput}
                    on:toggle={handleTimeToggle}
                />
            </div>
            <div class="result-grid__filters-row result-grid__filters-row--main">
                <div class="result-grid__filters-fields">
                    <DatePicker>
                        <DatePickerInput
                            id="result-grid-from-date"
                            size="sm"
                            labelText="From date"
                            placeholder="mm/dd/yyyy"
                            bind:value={fromDateInput}
                            on:input={(event) => {
                                fromDateInput = readInputValue(event);
                            }}
                        />
                    </DatePicker>
                    {#if enableTimeInput}
                        <TimePicker
                            size="sm"
                            labelText="From time"
                            placeholder="HH:MM"
                            bind:value={fromTimeInput}
                            on:input={(event) => {
                                fromTimeInput = readInputValue(event);
                            }}
                        />
                    {/if}
                    <DatePicker>
                        <DatePickerInput
                            id="result-grid-to-date"
                            size="sm"
                            labelText="To date"
                            placeholder="mm/dd/yyyy"
                            bind:value={toDateInput}
                            on:input={(event) => {
                                toDateInput = readInputValue(event);
                            }}
                        />
                    </DatePicker>
                    {#if enableTimeInput}
                        <TimePicker
                            size="sm"
                            labelText="To time"
                            placeholder="HH:MM"
                            bind:value={toTimeInput}
                            on:input={(event) => {
                                toTimeInput = readInputValue(event);
                            }}
                        />
                    {/if}
                </div>
                <div class="result-grid__filters-actions">
                    {#if isReloadingData && hasInitiallyLoaded}
                        <div class="result-grid__soft-loading" aria-live="polite">
                            <Loading withOverlay={false} small />
                        </div>
                    {/if}
                    <Button kind="primary" size="small" type="submit">Apply</Button>
                    <Button kind="secondary" size="small" type="reset">Clear</Button>
                </div>
            </div>
        </form>

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
