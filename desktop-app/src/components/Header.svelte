<script lang="ts">
    import { Header, HeaderNav, HeaderNavItem, HeaderUtilities } from 'carbon-components-svelte';
    import '../styles/header.css';
    import HeaderContactSelection from './HeaderContactSelection.svelte';
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
        <HeaderContactSelection />
    </HeaderUtilities>
</Header>
