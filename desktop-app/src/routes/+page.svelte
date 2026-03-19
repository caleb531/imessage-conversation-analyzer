<script lang="ts">
    import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';
    import { Button } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import InlineNotification from '../components/InlineNotification.svelte';
    import { getSelectedContacts } from '../lib/contacts.svelte';
    import {
        hasMissingRequiredPermissions,
        isPermissionStatusLoading,
        openPermissionSettings,
        permissionStatus,
        refreshPermissionStatus,
        requestContactsPermission
    } from '../lib/permissions.svelte';

    // Captures action-level errors so users can recover directly from the splash page.
    let actionErrorMessage = $state('');
    // Tracks whether the initial permissions bootstrap check has completed.
    let hasCheckedPermissions = $state(false);

    // Returns true when Contacts permission is currently granted.
    const isContactsGranted = $derived(Boolean(permissionStatus.value?.contacts.granted));
    // Returns true when Full Disk Access check can open the Messages database.
    const isFullDiskAccessGranted = $derived(
        Boolean(permissionStatus.value?.fullDiskAccess.granted)
    );
    // Returns whether Contacts can still be requested via native API prompt.
    const canRequestContacts = $derived(Boolean(permissionStatus.value?.contacts.canRequest));
    // Returns true when all required permissions have been granted.
    const isAllPermissionsGranted = $derived(Boolean(permissionStatus.value?.allGranted));

    // Human-readable status text shown for Contacts.
    const contactsStatusLabel = $derived(
        isContactsGranted
            ? 'Granted'
            : permissionStatus.value?.contacts.status === 'not_determined'
              ? 'Not requested yet'
              : permissionStatus.value?.contacts.status === 'restricted'
                ? 'Restricted by system policy'
                : permissionStatus.value?.contacts.status === 'denied'
                  ? 'Denied'
                  : 'Missing'
    );

    // Human-readable status text shown for Full Disk Access.
    const fullDiskStatusLabel = $derived(
        isFullDiskAccessGranted
            ? 'Granted'
            : permissionStatus.value?.fullDiskAccess.status === 'not_found'
              ? 'Messages database not found'
              : permissionStatus.value?.fullDiskAccess.status === 'denied'
                ? 'Denied'
                : 'Missing'
    );

    // Redirects users into the normal app flow once required permissions are available.
    async function redirectToMainFlow() {
        try {
            const contacts = await getSelectedContacts();
            await goto(resolve(contacts.length > 0 ? '/messages' : '/set-contacts'));
        } catch (error) {
            console.error('Failed to resolve selected contacts during startup redirect', error);
            await goto(resolve('/set-contacts'));
        }
    }

    // Refreshes permissions and enters normal app routing when all checks pass.
    async function refreshAndMaybeContinue() {
        const status = await refreshPermissionStatus();
        if (!hasMissingRequiredPermissions(status)) {
            await redirectToMainFlow();
        }
    }

    // Requests Contacts permission when requestable, otherwise opens Contacts settings.
    async function handleContactsButtonClick() {
        try {
            actionErrorMessage = '';
            if (canRequestContacts) {
                const status = await requestContactsPermission();
                if (!hasMissingRequiredPermissions(status)) {
                    await redirectToMainFlow();
                }
            } else {
                await openPermissionSettings('contacts');
                await refreshAndMaybeContinue();
            }
        } catch (error) {
            actionErrorMessage = error instanceof Error ? error.message : String(error);
        }
    }

    // Opens macOS Full Disk Access settings and re-checks status on return.
    async function handleFullDiskAccessButtonClick() {
        try {
            actionErrorMessage = '';
            await openPermissionSettings('full-disk-access');
            await refreshAndMaybeContinue();
        } catch (error) {
            actionErrorMessage = error instanceof Error ? error.message : String(error);
        }
    }

    // Re-runs backend permission checks after users update system settings manually.
    async function handleRecheckButtonClick() {
        try {
            actionErrorMessage = '';
            await refreshAndMaybeContinue();
        } catch (error) {
            actionErrorMessage = error instanceof Error ? error.message : String(error);
        }
    }

    // Loads the permission snapshot and routes users into app content when eligible.
    onMount(async () => {
        try {
            actionErrorMessage = '';
            await refreshAndMaybeContinue();
        } catch (error) {
            actionErrorMessage = error instanceof Error ? error.message : String(error);
        } finally {
            hasCheckedPermissions = true;
        }
    });
</script>

{#if hasCheckedPermissions && hasMissingRequiredPermissions(permissionStatus.value)}
    <section class="permissions-splash">
        <div class="permissions-splash__panel">
            <header class="permissions-splash__header">
                <h1>
                    <img class="permissions-splash__logo" src="logo-128x128@2x.png" alt="" /> iMessage
                    Conversation Analyzer
                </h1>
                <p>
                    Please grant the following permissions so the application can properly analyze
                    your message history.
                </p>
                <p class="permissions-splash__disclaimer">
                    <strong>
                        All processing is done locally on your machine, and no data is collected or
                        transmitted.
                    </strong>
                </p>
            </header>

            <div class="permissions-splash__rows">
                <section class="permissions-splash__row">
                    <div class="permissions-splash__info">
                        <h2>Contacts</h2>
                        <p>Needed to display the names of people in your conversations.</p>
                        <p class="permissions-splash__status">
                            Status: <strong>{contactsStatusLabel}</strong>
                        </p>
                        {#if permissionStatus.value?.contacts.detail}
                            <p class="permissions-splash__detail">
                                {permissionStatus.value.contacts.detail}
                            </p>
                        {/if}
                    </div>
                    <div class="permissions-splash__actions">
                        <Button
                            kind={isContactsGranted ? 'secondary' : 'primary'}
                            disabled={isPermissionStatusLoading.value || isContactsGranted}
                            onclick={handleContactsButtonClick}
                        >
                            {#if isContactsGranted}
                                Contacts Access Granted
                            {:else if canRequestContacts}
                                Allow Contacts Access
                            {:else}
                                Open Contacts Settings
                            {/if}
                        </Button>
                    </div>
                </section>

                <section class="permissions-splash__row">
                    <div class="permissions-splash__info">
                        <h2>Full Disk Access</h2>
                        <p>
                            Needed to read the iMessage database located at
                            <code>~/Library/Messages/chat.db</code>.
                        </p>
                        <p class="permissions-splash__status">
                            Status: <strong>{fullDiskStatusLabel}</strong>
                        </p>
                        {#if permissionStatus.value?.fullDiskAccess.detail}
                            <p class="permissions-splash__detail">
                                {permissionStatus.value.fullDiskAccess.detail}
                            </p>
                        {/if}
                    </div>
                    <div class="permissions-splash__actions">
                        <Button
                            kind={isFullDiskAccessGranted ? 'secondary' : 'primary'}
                            disabled={isPermissionStatusLoading.value || isFullDiskAccessGranted}
                            onclick={handleFullDiskAccessButtonClick}
                        >
                            {#if isFullDiskAccessGranted}
                                Full Disk Access Granted
                            {:else}
                                Open Full Disk Access Settings
                            {/if}
                        </Button>
                    </div>
                </section>
            </div>

            <footer class="permissions-splash__footer">
                <Button
                    kind="tertiary"
                    disabled={isPermissionStatusLoading.value}
                    onclick={handleRecheckButtonClick}
                >
                    Re-check Permissions
                </Button>
                {#if isAllPermissionsGranted}
                    <span class="permissions-splash__ready"
                        >All required permissions are granted.</span
                    >
                {/if}
            </footer>

            {#if actionErrorMessage}
                <div class="permissions-splash__notification">
                    <InlineNotification
                        kind="error"
                        title="Permission check failed"
                        subtitle={actionErrorMessage}
                    />
                </div>
            {/if}
        </div>
    </section>
{/if}

<style>
    .permissions-splash__panel {
        width: 100%;
        max-width: 50rem;
        margin: 0 auto;
        background: var(--color-surface-secondary);
        border: 1px solid var(--color-border-secondary);
        border-radius: 0.75rem;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1.5rem;
    }

    .permissions-splash__header {
        text-align: left;
    }

    .permissions-splash__header h1 {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0.75rem;
        margin: 0;
        margin-bottom: 1rem;
    }

    .permissions-splash__logo {
        height: 3rem;
    }

    .permissions-splash__disclaimer {
        margin-top: 1rem;
        border-radius: 10px;
        padding: 10px 15px;
        background-color: var(--color-note);
    }

    .permissions-splash__rows {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .permissions-splash__row {
        display: flex;
        justify-content: space-between;
        gap: 1.5rem;
        border: 1px solid var(--color-border-secondary);
        border-radius: 0.75rem;
        padding: 1.25rem;
    }

    .permissions-splash__info {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .permissions-splash__info h2 {
        margin: 0;
        text-align: left;
    }

    .permissions-splash__info p {
        margin: 0;
    }

    .permissions-splash__status {
        color: var(--color-text-secondary);
    }

    .permissions-splash__detail {
        color: var(--color-text-secondary);
        font-size: 0.875rem;
    }

    .permissions-splash__actions {
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }

    .permissions-splash__footer {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .permissions-splash__ready {
        color: var(--color-text-secondary);
        font-size: 0.875rem;
    }

    .permissions-splash__notification {
        margin-top: 0.5rem;
    }

    @media (max-width: 880px) {
        .permissions-splash__row {
            flex-direction: column;
        }

        .permissions-splash__actions {
            justify-content: flex-start;
            min-width: 0;
        }
    }
</style>
