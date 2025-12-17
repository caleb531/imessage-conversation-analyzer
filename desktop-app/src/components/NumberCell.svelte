<script lang="ts">
    const { row, column } = $props<{ value: number }>();
</script>

<span class="number-cell">{Intl.NumberFormat().format(row[column.id])}</span>
