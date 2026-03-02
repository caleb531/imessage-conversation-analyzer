<script lang="ts">
    import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';
    import { onMount } from 'svelte';
    import { getSelectedContacts } from '../lib/contacts.svelte';

    onMount(async () => {
        const contacts = await getSelectedContacts();
        if (contacts.length > 0) {
            await goto(resolve('/message-totals'));
        } else {
            await goto(resolve('/set-contact'));
        }
    });
</script>
