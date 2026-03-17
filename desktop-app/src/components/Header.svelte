<script lang="ts">
    import { Header, HeaderNav, HeaderNavItem, HeaderUtilities } from 'carbon-components-svelte';
    import '../styles/header.css';
    import HeaderContactSelection from './HeaderContactSelection.svelte';
</script>

<Header platformName="ICA">
    <HeaderNav>
        <HeaderNavItem href="/messages">Messages</HeaderNavItem>
        <HeaderNavItem href="/attachments">Attachments</HeaderNavItem>
        <HeaderNavItem href="/emojis">Emojis</HeaderNavItem>
        <HeaderNavItem href="/phrases">Phrases</HeaderNavItem>
        <HeaderNavItem href="/totals-by-day">Totals by Day</HeaderNavItem>
        <HeaderNavItem href="/transcript">Transcript</HeaderNavItem>
    </HeaderNav>
    <HeaderUtilities>
        <HeaderContactSelection />
    </HeaderUtilities>
</Header>
