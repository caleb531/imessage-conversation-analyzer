<script lang="ts">
    // Props consumed by a grid cell renderer for numeric values.
    interface Props {
        row: Record<string, unknown>;
        column: { id: string };
    }

    // Current row payload and target column metadata from the grid.
    const { row, column }: Props = $props();

    // Cell value normalized to a number so Intl formatting receives a valid input type.
    const numericValue = $derived(Number(row[column.id] ?? 0));
</script>

<span class="number-cell">{Intl.NumberFormat().format(numericValue)}</span>
