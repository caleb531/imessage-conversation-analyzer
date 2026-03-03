<script lang="ts">
    import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';
    import { onMount } from 'svelte';
    import { getSelectedContacts } from '../lib/contacts.svelte';

    // Redirects first-load users based on whether any contacts are already selected.
    onMount(async () => {
        try {
            const contacts = await getSelectedContacts();
            await goto(resolve(contacts.length > 0 ? '/message-totals' : '/set-contacts'));
        } catch (error) {
            console.error('Failed to resolve selected contacts during startup redirect', error);
            await goto(resolve('/set-contacts'));
        }
    });
</script>
