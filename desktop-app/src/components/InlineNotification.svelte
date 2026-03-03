<script lang="ts">
    import {
        InlineNotification as CarbonInlineNotification,
        NotificationActionButton
    } from 'carbon-components-svelte';

    // Extracts the Carbon component prop type so this wrapper stays API-compatible.
    type CarbonInlineNotificationProps = InstanceType<
        typeof CarbonInlineNotification
    >['$$prop_def'];
    // Wrapper props that add an optional action callback while keeping Carbon props.
    type Props = Omit<CarbonInlineNotificationProps, 'lowContrast'> & {
        actionLabel?: string;
        onAction?: (_event: MouseEvent) => void;
    };

    // Wrapper props forwarded to Carbon with low-contrast mode always enabled.
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
