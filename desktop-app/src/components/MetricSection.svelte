<script lang="ts">
    import type { Snippet } from 'svelte';

    // Allowed heading levels for semantic section titles.
    type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6;

    // Public API for metric sections that own heading semantics and optional descriptions.
    interface Props {
        title: string;
        description?: string;
        level?: HeadingLevel;
        children?: Snippet;
    }

    // Component inputs with defaults for common metric-page usage.
    let { title, description = '', level = 2, children }: Props = $props();

    // Computes the concrete heading tag name from the requested semantic level.
    function getHeadingTag(headingLevel: HeadingLevel): 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' {
        return `h${headingLevel}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
    }
</script>

<section class="metric-section">
    <header>
        <svelte:element this={getHeadingTag(level)}>{title}</svelte:element>
        {#if description}
            <p>{description}</p>
        {/if}
    </header>

    {@render children?.()}
</section>
