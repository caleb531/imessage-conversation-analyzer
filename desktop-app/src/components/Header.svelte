<script lang="ts">
    import { Header, HeaderNav, HeaderNavItem, HeaderUtilities } from 'carbon-components-svelte';
    import '../styles/header.css';
    import HeaderContactSelection from './HeaderContactSelection.svelte';
</script>

<Header platformName="ICA">
    <HeaderNav>
        <HeaderNavItem href="/message-totals">Messages</HeaderNavItem>
        <HeaderNavItem href="/attachment-totals">Attachments</HeaderNavItem>
        <HeaderNavItem href="/most-frequent-emojis">Emojis</HeaderNavItem>
        <HeaderNavItem href="/count-phrases">Phrases</HeaderNavItem>
        <HeaderNavItem href="/totals-by-day">Totals by Day</HeaderNavItem>
        <HeaderNavItem href="/transcript">Transcript</HeaderNavItem>
    </HeaderNav>
    <HeaderUtilities>
        <HeaderContactSelection />
    </HeaderUtilities>
</Header>
