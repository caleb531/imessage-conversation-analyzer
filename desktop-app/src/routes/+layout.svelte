<script lang="ts">
    const { children } = $props();
    import '../styles/layout.css';
</script>

<main>
    <section>
        {#if children}
            {@render children()}
        {/if}
    </section>
</main>
