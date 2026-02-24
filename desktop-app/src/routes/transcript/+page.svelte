<script lang="ts">
    import { invoke } from '@tauri-apps/api/core';
    import { revealItemInDir } from '@tauri-apps/plugin-opener';
    import { Button } from 'carbon-components-svelte';
    import InlineNotification from '../../components/InlineNotification.svelte';
    import { invokeIcaCsvToFile, MissingContactError } from '../../lib/cli';

    const baseFilename = 'transcript.csv';

    let isExporting = $state(false);
    let errorMessage = $state('');
    let successMessage = $state('');
    let exportedFilePath = $state('');

    async function exportTranscript(event: Event) {
        event.preventDefault();
        isExporting = true;
        errorMessage = '';
        successMessage = '';

        try {
            const outputPath = await invoke<string>('resolve_download_output_path', {
                baseName: baseFilename
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
                Export your full conversation transcript to CSV in Downloads. The filename will be
                incremented when needed (for example, transcript-1.csv).
            </p>
        </header>

        <form class="transcript-export__form" onsubmit={exportTranscript}>
            <Button type="submit" kind="primary" disabled={isExporting}>
                {isExporting ? 'Exporting…' : 'Export Transcript CSV'}
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
    }

    .transcript-export__notification {
        width: 100%;
        max-width: 56rem;
        margin: 0 auto;
        display: flex;
        justify-content: center;
    }
</style>
