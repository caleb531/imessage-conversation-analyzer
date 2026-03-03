<script lang="ts">
    import { Content, Theme } from 'carbon-components-svelte';
    import 'carbon-components-svelte/css/all.css';
    import Header from '../components/Header.svelte';
    import '../styles/colors.css';
    import '../styles/layout.css';
    import '../styles/utility-classes.css';
    // Routed child content rendered inside the layout shell.
    const { children } = $props();
</script>

<Theme theme="g100">
    <Header />
    <Content>
        <section>
            {@render children?.()}
        </section>
    </Content>
</Theme>
