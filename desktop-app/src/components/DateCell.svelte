<script lang="ts">
    const { row, column } = $props<{ value: number }>();
</script>

<span class="date-cell"
    >{new Intl.DateTimeFormat('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(row[column.id]))}</span
>
