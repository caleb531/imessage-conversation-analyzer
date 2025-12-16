<script lang="ts">
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import { getSelectedContact } from '../lib/contacts.svelte';

    onMount(async () => {
        const contact = await getSelectedContact();
        await goto(contact ? '/call-cli' : '/set-contact');
    });
</script>
