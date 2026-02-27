<script lang="ts">
    import {
        Header,
        HeaderNav,
        HeaderNavItem,
        HeaderUtilities,
        Link
    } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import { ensureSelectedContactsLoaded, selectedContacts } from '../lib/contacts.svelte';
    import '../styles/header.css';
    const hasContacts = $derived(selectedContacts.value.length > 0);
    const contactLabel = $derived(
        selectedContacts.value.length === 0
            ? 'No selected contacts'
            : selectedContacts.value.length === 1
              ? selectedContacts.value[0]
              : `${selectedContacts.value.length} contacts selected`
    );
    const actionLabel = $derived(hasContacts ? 'Change contacts' : 'Set contacts');

    onMount(() => {
        ensureSelectedContactsLoaded().catch((error) => {
            console.error('Failed to load selected contacts', error);
        });
    });
</script>

<Header platformName="ICA">
    <HeaderNav>
        <HeaderNavItem href="/message-totals">Message Totals</HeaderNavItem>
        <HeaderNavItem href="/attachment-totals">Attachment Totals</HeaderNavItem>
        <HeaderNavItem href="/most-frequent-emojis">Emojis</HeaderNavItem>
        <HeaderNavItem href="/totals-by-day">Totals by Day</HeaderNavItem>
        <HeaderNavItem href="/transcript">Transcript</HeaderNavItem>
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
