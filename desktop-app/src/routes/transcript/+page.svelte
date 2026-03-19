<script lang="ts">
    import { invoke } from '@tauri-apps/api/core';
    import { revealItemInDir } from '@tauri-apps/plugin-opener';
    import { Button, Select, SelectItem } from 'carbon-components-svelte';
    import DateRangeFields from '../../components/DateRangeFields.svelte';
    import InlineNotification from '../../components/InlineNotification.svelte';
    import { invokeIcaCsvToFile, MissingContactError } from '../../lib/cli';
    import { buildDateFilterArgs } from '../../lib/dateFilters';

    // Base file stem used when generating the export filename.
    const baseFilename = 'transcript';

    // Tracks export progress to disable controls while work is running.
    let isExporting = $state(false);
    // Selected output format for the transcript export.
    let format = $state<'csv' | 'xlsx'>('csv');
    // User-entered date range values consumed by date filter arg builder.
    let fromDateInput = $state('');
    let toDateInput = $state('');
    // Surfaces date filter persistence failures from DateRangeFields.
    let dateFilterPersistenceError = $state('');
    // UI feedback state for success/error notifications.
    let errorMessage = $state('');
    let successMessage = $state('');
    // Stores the most recent export path for "Reveal in Finder" action.
    let exportedFilePath = $state('');

    // Runs transcript export with optional date filters and selected file format.
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
            const filterArgs = buildDateFilterArgs({
                fromDate: fromDateInput,
                toDate: toDateInput
            });
            await invokeIcaCsvToFile(['transcript', ...filterArgs], outputPath);
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

    // Reveals the most recently exported file in Finder.
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

    // Clears both date filter inputs without triggering an export.
    function clearDateFilters() {
        fromDateInput = '';
        toDateInput = '';
    }
</script>

<section class="transcript-export">
    <header>
        <h2>Transcript</h2>
        <p class="transcript-export__description">
            Export your full conversation transcript. The exported file will be saved to your
            Downloads folder.
        </p>
    </header>

    <form class="transcript-export__form" onsubmit={exportTranscript}>
        <div class="transcript-export__row transcript-export__row--dates">
            <DateRangeFields
                fromDateInputId="transcript-from-date"
                toDateInputId="transcript-to-date"
                dateFilterPersistenceKey="transcript"
                bind:persistenceError={dateFilterPersistenceError}
                bind:fromDate={fromDateInput}
                bind:toDate={toDateInput}
                disabled={isExporting}
            />
            <Button
                kind="secondary"
                size="small"
                type="button"
                disabled={isExporting}
                onclick={clearDateFilters}
            >
                Clear
            </Button>
        </div>

        <div class="transcript-export__row transcript-export__row--actions">
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
        </div>
    </form>

    {#if dateFilterPersistenceError}
        <aside class="transcript-export__notification">
            <InlineNotification
                kind="error"
                title="Date filter persistence failed"
                subtitle={dateFilterPersistenceError}
            />
        </aside>
    {/if}

    {#if successMessage}
        <aside class="transcript-export__notification">
            <InlineNotification
                kind="success"
                title="Export complete"
                subtitle={successMessage}
                actionLabel="Reveal in Finder"
                onAction={openDownloads}
            />
        </aside>
    {/if}

    {#if errorMessage}
        <aside class="transcript-export__notification">
            <InlineNotification kind="error" title="Export failed" subtitle={errorMessage} />
        </aside>
    {/if}
</section>

<style>
    .transcript-export {
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
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1rem;
    }

    .transcript-export__row {
        display: flex;
        width: 100%;
        justify-content: center;
    }

    .transcript-export__row--actions {
        align-items: flex-end;
        gap: 1rem;
    }

    .transcript-export__row--dates {
        align-items: flex-end;
        gap: 1rem;
    }

    .transcript-export__format {
        width: 12rem;
    }

    .transcript-export__notification {
        width: 100%;
        display: flex;
        justify-content: center;
    }
</style>
