<script lang="ts">
    // Props consumed by a grid cell renderer for date values.
    interface Props {
        row: Record<string, unknown>;
        column: { id: string };
    }

    // Current row payload and target column metadata from the grid.
    const { row, column }: Props = $props();

    // Cell value normalized to a string for safe Date construction.
    const dateValue = $derived(String(row[column.id] ?? ''));
</script>

<span class="date-cell"
    >{new Intl.DateTimeFormat('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(dateValue))}</span
>
