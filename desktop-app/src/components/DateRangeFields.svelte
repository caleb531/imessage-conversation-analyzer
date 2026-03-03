<script lang="ts">
    import { DatePicker, DatePickerInput, TooltipIcon } from 'carbon-components-svelte';
    import Information from 'carbon-icons-svelte/lib/Information.svelte';

    // Public API for the shared date-range picker pair.
    interface Props {
        fromDate?: string;
        toDate?: string;
        disabled?: boolean;
        fromDateInputId?: string;
        toDateInputId?: string;
    }

    // Bindable values allow parent components to fully control the selected dates.
    let {
        fromDate = $bindable(''),
        toDate = $bindable(''),
        disabled = false,
        fromDateInputId = 'from-date',
        toDateInputId = 'to-date'
    }: Props = $props();
</script>

<div class="date-range-fields">
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
</div>

<style>
    .date-range-fields {
        display: grid;
        grid-template-columns: repeat(2, minmax(9rem, 1fr));
        gap: 1rem 0.5rem;
        width: auto;
        max-width: none;
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
