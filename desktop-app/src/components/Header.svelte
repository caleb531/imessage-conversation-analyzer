<script lang="ts">
    import {
        Header,
        HeaderNav,
        HeaderNavItem,
        HeaderUtilities,
        Link
    } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { ensureSelectedContactLoaded, selectedContact } from '../lib/contacts.svelte';
    import '../styles/header.css';
    const hasContact = $derived(Boolean(selectedContact.value));
    const contactLabel = $derived(selectedContact.value ?? 'No selected contact');
    const actionLabel = $derived(hasContact ? 'Change contact' : 'Set contact');

    onMount(() => {
        ensureSelectedContactLoaded().catch((error) => {
            console.error('Failed to load selected contact', error);
        });
    });
</script>

<Header platformName="iMessage Conversation Analyzer">
    <HeaderNav>
        <HeaderNavItem href="/call-cli">Call CLI</HeaderNavItem>
    </HeaderNav>
    <HeaderUtilities>
        <div class="app-header__contact">
            <span class="app-header__contact-name">{contactLabel}</span>
            <Link class="app-header__contact-link" href="/set-contact">
                {actionLabel}
            </Link>
        </div>
    </HeaderUtilities>
</Header>

<style>
    .app-header__contact {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.25rem;
    }

    .app-header__contact-name {
        font-size: 0.875rem;
        line-height: 1.25rem;
    }

    :global(.app-header__contact-link) {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
</style>
