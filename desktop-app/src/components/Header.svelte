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

<Header platformName="ICA">
    <HeaderNav>
        <HeaderNavItem href="/message-totals">Message Totals</HeaderNavItem>
        <HeaderNavItem href="/attachment-totals">Attachment Totals</HeaderNavItem>
        <HeaderNavItem href="/most-frequent-emojis">Emojis</HeaderNavItem>
        <HeaderNavItem href="/totals-by-day">Totals by Day</HeaderNavItem>
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
