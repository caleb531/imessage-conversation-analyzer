<script lang="ts">
    import {
        InlineNotification as CarbonInlineNotification,
        NotificationActionButton
    } from 'carbon-components-svelte';

    type CarbonInlineNotificationProps = InstanceType<
        typeof CarbonInlineNotification
    >['$$prop_def'];
    type Props = Omit<CarbonInlineNotificationProps, 'lowContrast'> & {
        actionLabel?: string;
        onAction?: (event: MouseEvent) => void;
    };

    let { actionLabel, onAction, ...props }: Props = $props();
</script>

<CarbonInlineNotification
    {...props}
    lowContrast
    on:close
    on:click
    on:mouseover
    on:mouseenter
    on:mouseleave
>
    {#if actionLabel}
        <NotificationActionButton slot="actions" onclick={onAction}>
            {actionLabel}
        </NotificationActionButton>
    {/if}
</CarbonInlineNotification>
