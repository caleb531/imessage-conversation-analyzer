<script lang="ts">
    import { invoke } from '@tauri-apps/api/core';
    import { revealItemInDir } from '@tauri-apps/plugin-opener';
    import { Button, Select, SelectItem } from 'carbon-components-svelte';
    import InlineNotification from '../../components/InlineNotification.svelte';
    import { invokeIcaCsvToFile, MissingContactError } from '../../lib/cli';

    const baseFilename = 'transcript';

    let isExporting = $state(false);
    let format = $state<'csv' | 'xlsx'>('csv');
    let errorMessage = $state('');
    let successMessage = $state('');
    let exportedFilePath = $state('');

    async function exportTranscript(event: Event) {
        event.preventDefault();
        isExporting = true;
        errorMessage = '';
        successMessage = '';

        try {
            const filename = `${baseFilename}.${format}`;
            const outputPath = await invoke<string>('resolve_download_output_path', {
                baseName: filename
            });
            await invokeIcaCsvToFile(['transcript'], outputPath);
            exportedFilePath = outputPath;
            successMessage = `Transcript exported to ${outputPath}`;
        } catch (error) {
            if (error instanceof MissingContactError) {
                errorMessage = error.message;
            } else {
                errorMessage = error instanceof Error ? error.message : String(error);
            }
        } finally {
            isExporting = false;
        }
    }

    async function openDownloads(event: Event) {
        event.preventDefault();
        if (!exportedFilePath) {
            return;
        }
        try {
            await revealItemInDir(exportedFilePath);
        } catch (error) {
            errorMessage = error instanceof Error ? error.message : String(error);
        }
    }
</script>

<section class="transcript-export">
    <div class="transcript-export__content">
        <header>
            <h2>Transcript</h2>
            <p class="transcript-export__description">
                Export your full conversation transcript in your selected format to Downloads. The
                filename will be incremented when needed (for example, transcript-1.csv).
            </p>
        </header>

        <form class="transcript-export__form" onsubmit={exportTranscript}>
            <div class="transcript-export__format">
                <Select labelText="Format" bind:selected={format} disabled={isExporting}>
                    <SelectItem value="csv" text="CSV" />
                    <SelectItem value="xlsx" text="Excel" />
                </Select>
            </div>

            <Button type="submit" kind="primary" disabled={isExporting}>
                {#if isExporting}
                    Exporting…
                {:else}
                    Export Transcript
                {/if}
            </Button>
        </form>

        {#if successMessage}
            <div class="transcript-export__notification">
                <InlineNotification
                    kind="success"
                    title="Export complete"
                    subtitle={successMessage}
                    actionLabel="Reveal in Finder"
                    onAction={openDownloads}
                />
            </div>
        {/if}

        {#if errorMessage}
            <div class="transcript-export__notification">
                <InlineNotification kind="error" title="Export failed" subtitle={errorMessage} />
            </div>
        {/if}
    </div>
</section>

<style>
    .transcript-export {
        align-items: center;
    }

    .transcript-export__content {
        width: 100%;
        max-width: 56rem;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .transcript-export__description {
        max-width: 44rem;
        margin: 0 auto;
    }

    .transcript-export__form {
        margin-top: 1.5rem;
        display: flex;
        flex-direction: row;
        align-items: flex-end;
        justify-content: center;
        gap: 1rem;
    }

    .transcript-export__format {
        width: 12rem;
    }

    .transcript-export__notification {
        width: 100%;
        max-width: 56rem;
        margin: 0 auto;
        display: flex;
        justify-content: center;
    }
</style>
