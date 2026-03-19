<script lang="ts">
    import { DatePicker, DatePickerInput, TooltipIcon } from 'carbon-components-svelte';
    import Information from 'carbon-icons-svelte/lib/Information.svelte';
    import { onMount, untrack } from 'svelte';
    import {
        getResultGridDateFilterState,
        setResultGridDateFilterState
    } from '../lib/resultGridDateFilters.svelte';

    // Public API for the shared date-range picker pair.
    interface Props {
        fromDate?: string;
        toDate?: string;
        disabled?: boolean;
        fromDateInputId?: string;
        toDateInputId?: string;
        dateFilterPersistenceKey?: string;
        persistenceError?: string;
        hasLoadedPersistedDateFilters?: boolean;
    }

    // Bindable values allow parent components to fully control the selected dates.
    let {
        fromDate = $bindable(''),
        toDate = $bindable(''),
        disabled = false,
        fromDateInputId = 'from-date',
        toDateInputId = 'to-date',
        dateFilterPersistenceKey,
        // eslint-disable-next-line no-useless-assignment
        persistenceError = $bindable(),
        hasLoadedPersistedDateFilters = $bindable()
    }: Props = $props();

    // Tracks the latest save operation so stale async failures do not overwrite newer outcomes.
    let saveRequestVersion = $state(0);

    // Persists current field values when a persistence key is provided.
    async function persistDateFilterState(nextFromDate: string, nextToDate: string) {
        if (!dateFilterPersistenceKey) {
            return;
        }

        saveRequestVersion += 1;
        const requestVersion = saveRequestVersion;
        persistenceError = '';

        try {
            await setResultGridDateFilterState(dateFilterPersistenceKey, {
                fromDate: nextFromDate,
                toDate: nextToDate
            });
        } catch (error) {
            if (requestVersion === saveRequestVersion) {
                persistenceError = error instanceof Error ? error.message : String(error);
            }
        }
    }

    // Loads persisted values once so parent components can gate initial data loads.
    onMount(async () => {
        if (!dateFilterPersistenceKey) {
            hasLoadedPersistedDateFilters = true;
            return;
        }

        try {
            const persistedDateFilters =
                await getResultGridDateFilterState(dateFilterPersistenceKey);
            fromDate = persistedDateFilters.fromDate;
            toDate = persistedDateFilters.toDate;
        } catch (error) {
            persistenceError = error instanceof Error ? error.message : String(error);
        } finally {
            hasLoadedPersistedDateFilters = true;
        }
    });

    // Saves value changes after initial hydration to avoid overwriting persisted values on mount.
    $effect(() => {
        if (!hasLoadedPersistedDateFilters) {
            return;
        }

        const currentFromDate = fromDate;
        const currentToDate = toDate;

        untrack(() => {
            void persistDateFilterState(currentFromDate, currentToDate);
        });
    });
</script>

<fieldset class="date-range-fields">
    <DatePicker datePickerType="single" dateFormat="m/d/Y" bind:value={fromDate}>
        <DatePickerInput
            id={fromDateInputId}
            size="sm"
            labelText="From date"
            placeholder="mm/dd/yyyy"
            {disabled}
        >
            {#snippet labelChildren()}
                <span class="date-range-fields__label">
                    <span class="date-range-fields__label-text">From date</span>
                    <TooltipIcon tooltipText="Starting from midnight on the specified start date">
                        <Information />
                    </TooltipIcon>
                </span>
            {/snippet}
        </DatePickerInput>
    </DatePicker>

    <DatePicker datePickerType="single" dateFormat="m/d/Y" bind:value={toDate}>
        <DatePickerInput
            id={toDateInputId}
            size="sm"
            labelText="To date"
            placeholder="mm/dd/yyyy"
            {disabled}
        >
            {#snippet labelChildren()}
                <span class="date-range-fields__label">
                    <span class="date-range-fields__label-text">To date</span>
                    <TooltipIcon tooltipText="Up to (but not including) the specified end date">
                        <Information />
                    </TooltipIcon>
                </span>
            {/snippet}
        </DatePickerInput>
    </DatePicker>
</fieldset>

<style>
    .date-range-fields {
        border: 0;
        display: grid;
        grid-template-columns: repeat(2, minmax(9rem, 1fr));
        gap: 1rem 0.5rem;
        margin: 0;
        width: auto;
        max-width: none;
        padding: 0;
        align-items: end;
    }

    .date-range-fields__label {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }

    .date-range-fields :global(.bx--date-picker.bx--date-picker--single .bx--date-picker__input) {
        width: 9rem;
    }
</style>
