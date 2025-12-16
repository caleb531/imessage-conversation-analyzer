<script lang="ts">
    import { Theme } from 'carbon-components-svelte';
    import 'carbon-components-svelte/css/all.css';
    import type { ThemeProps } from 'carbon-components-svelte/src/Theme/Theme.svelte';
    import '../styles/layout.css';
    const { children } = $props();
    let theme: ThemeProps['theme'] = 'g100';
</script>

<Theme {theme}>
    <main data-carbon-theme="g100">
        <section>
            {#if children}
                {@render children()}
            {/if}
        </section>
    </main>
</Theme>
