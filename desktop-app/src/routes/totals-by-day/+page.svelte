<script lang="ts">
    import ResultGrid from '../../components/ResultGrid.svelte';
</script>

<ResultGrid
    title="Totals by Day"
    description="See your message totals, per person or overall, for each day you've messaged"
    command={['totals_by_day']}
/>
