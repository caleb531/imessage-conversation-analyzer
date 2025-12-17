<script lang="ts">
    import ResultGrid from '../../components/ResultGrid.svelte';
</script>

<ResultGrid
    title="Message Totals"
    description="Review aggregated conversation metrics like the total number of messages sent and received."
    command={['message_totals']}
/>
