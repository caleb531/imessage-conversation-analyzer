<script lang="ts">
    import { afterNavigate, goto } from '$app/navigation';
    import { resolve } from '$app/paths';
    import { Content, Theme } from 'carbon-components-svelte';
    import 'carbon-components-svelte/css/all.css';
    import { onMount } from 'svelte';
    import Header from '../components/Header.svelte';
    import {
        hasMissingRequiredPermissions,
        refreshPermissionStatus
    } from '../lib/permissions.svelte';
    import '../styles/colors.css';
    import '../styles/layout.css';
    import '../styles/utility-classes.css';
    // Routed child content rendered inside the layout shell.
    const { children } = $props();

    // Tracks whether the current route is the root splash route.
    let isRootRoute = $state(false);
    // Tracks whether the initial permission gate check has completed.
    let hasPermissionGateBootstrapped = $state(false);

    // Returns whether the current location path is the root route.
    function isCurrentPathRootRoute(): boolean {
        return window.location.pathname === '/';
    }

    // Enforces route preemption based on required permission state.
    async function enforcePermissionGate() {
        isRootRoute = isCurrentPathRootRoute();
        const status = await refreshPermissionStatus();
        const hasMissingPermissions = hasMissingRequiredPermissions(status);

        if (hasMissingPermissions && !isRootRoute) {
            await goto(resolve('/'), { replaceState: true, noScroll: true });
            isRootRoute = true;
        }
    }

    // Initializes the permission gate and re-runs checks after client navigations.
    onMount(() => {
        const runGate = async () => {
            try {
                await enforcePermissionGate();
            } catch (error) {
                console.error('Failed to enforce permissions route gate', error);
            } finally {
                hasPermissionGateBootstrapped = true;
            }
        };

        void runGate();

        afterNavigate(() => {
            void runGate();
        });
    });
</script>

<Theme theme="g100">
    {#if hasPermissionGateBootstrapped}
        {#if isRootRoute}
            {@render children?.()}
        {:else}
            <Header />
            <Content>
                <section>
                    {@render children?.()}
                </section>
            </Content>
        {/if}
    {/if}
</Theme>
