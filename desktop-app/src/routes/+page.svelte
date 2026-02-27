<script lang="ts">
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import { getSelectedContacts } from '../lib/contacts.svelte';

    onMount(async () => {
        const contacts = await getSelectedContacts();
        await goto(contacts.length > 0 ? '/message-totals' : '/set-contact');
    });
</script>
