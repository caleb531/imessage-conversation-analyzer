<script lang="ts">
    import { Content, Theme } from 'carbon-components-svelte';
    import 'carbon-components-svelte/css/all.css';
    import type { ThemeProps } from 'carbon-components-svelte/src/Theme/Theme.svelte';
    import Header from '../components/Header.svelte';
    import '../styles/layout.css';
    const { children } = $props();
    let theme: ThemeProps['theme'] = 'g100';
</script>

<Theme {theme}>
    <Header />
    <Content>
        <section>
            {#if children}
                {@render children()}
            {/if}
        </section>
    </Content>
</Theme>
