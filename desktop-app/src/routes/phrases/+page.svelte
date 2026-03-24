<script lang="ts">
    import { Checkbox, Tag, TextInput } from 'carbon-components-svelte';
    import { onMount } from 'svelte';
    import InlineNotification from '../../components/InlineNotification.svelte';
    import MetricSection from '../../components/MetricSection.svelte';
    import ResultGrid from '../../components/ResultGrid.svelte';
    import { getCountPhrasesState, setCountPhrasesState } from '../../lib/countPhrases.svelte';

    // Stores the current freeform phrase value before users add it to the active list.
    let phraseInput = $state('');
    // Tracks all phrase entries used to build the analyzer command.
    let phrases = $state<string[]>([]);
    // Controls whether every phrase is interpreted as a regular expression.
    let useRegex = $state(false);
    // Controls whether matching uses case-sensitive comparisons.
    let caseSensitive = $state(false);
    // Tracks whether the user has attempted to construct a tag and failed (used to show empty errors).
    let hasAttemptedAdd = $state(false);
    // Tracks persistence load/save failures shown to users inline.
    let persistenceError = $state('');
    // Indicates that persisted state hydration has completed.
    let hasInitializedPersistence = $state(false);
    // Tracks most recent save request so stale async failures can be ignored.
    let saveRequestVersion = 0;

    // Returns true when at least one phrase is available for analysis.
    const isReadyToAnalyze = $derived(phrases.length > 0);
    // Recomputes the analyzer command whenever phrases or toggles change.
    const command = $derived(buildCountPhrasesCommand(phrases, useRegex, caseSensitive));

    // Validates inputs dynamically
    const normalizedInput = $derived(phraseInput.trim());
    const isDuplicate = $derived(
        phrases.some((phrase) => phrase.toLocaleLowerCase() === normalizedInput.toLocaleLowerCase())
    );

    // Determines usability of add action.
    const canAddPhrase = $derived(normalizedInput.length > 0 && !isDuplicate);

    // Resolves what error message users should see based on action timing + input.
    const phraseErrorMessage = $derived.by(() => {
        if (isDuplicate) {
            return 'That phrase is already in the list.';
        }
        if (hasAttemptedAdd && normalizedInput.length === 0) {
            return 'Enter a phrase before adding it.';
        }
        return '';
    });

    // Clear empty validation error if user resumes typing.
    $effect(() => {
        if (phraseInput.length > 0) {
            hasAttemptedAdd = false;
        }
    });

    // Loads any saved phrase-builder state before enabling autosave effects.
    onMount(async () => {
        try {
            const persistedState = await getCountPhrasesState();
            phrases = [...persistedState.phrases];
            useRegex = persistedState.useRegex;
            caseSensitive = persistedState.caseSensitive;
        } catch (error) {
            persistenceError = error instanceof Error ? error.message : String(error);
        } finally {
            hasInitializedPersistence = true;
        }
    });

    // Persists current route state and only surfaces failures from the latest request.
    async function persistCountPhrasesState(
        activePhrases: string[],
        shouldUseRegex: boolean,
        shouldUseCaseSensitive: boolean
    ) {
        // Captures the current request sequence to avoid showing stale save errors.
        const requestVersion = saveRequestVersion + 1;
        saveRequestVersion = requestVersion;
        persistenceError = '';

        try {
            await setCountPhrasesState({
                phrases: activePhrases,
                useRegex: shouldUseRegex,
                caseSensitive: shouldUseCaseSensitive
            });
        } catch (error) {
            if (requestVersion === saveRequestVersion) {
                persistenceError = error instanceof Error ? error.message : String(error);
            }
        }
    }

    // Automatically persists state after initial hydration whenever phrases or toggles change.
    $effect(() => {
        if (!hasInitializedPersistence) {
            return;
        }

        void persistCountPhrasesState([...phrases], useRegex, caseSensitive);
    });

    // Converts local UI state into the CLI argument list expected by `count_phrases`.
    function buildCountPhrasesCommand(
        activePhrases: string[],
        shouldUseRegex: boolean,
        shouldUseCaseSensitive: boolean
    ): string[] {
        const nextCommand = ['count_phrases'];

        for (const phrase of activePhrases) {
            nextCommand.push(phrase);
        }

        if (shouldUseRegex) {
            nextCommand.push('--use-regex');
        }

        if (shouldUseCaseSensitive) {
            nextCommand.push('--case-sensitive');
        }

        return nextCommand;
    }

    // Adds the current input phrase to the active list when it passes validation.
    function addPhrase() {
        if (!canAddPhrase) {
            hasAttemptedAdd = true;
            return;
        }

        phrases = [...phrases, normalizedInput];
        phraseInput = '';
        hasAttemptedAdd = false;
    }

    // Removes a phrase from the active list by exact value.
    function removePhrase(phraseToRemove: string) {
        phrases = phrases.filter((phrase) => phrase !== phraseToRemove);
    }
</script>

<MetricSection
    title="Phrases"
    description="Count how often one or more custom phrases appear in your conversation."
    level={2}
>
    <ResultGrid
        {command}
        isReady={isReadyToAnalyze}
        notReadyMessage="Add phrases to begin analysis."
        dateFilterPersistenceKey="phrases"
    >
        {#snippet parameters()}
            <div class="phrases-params">
                <div class="phrases-params__add-row" class:has-error={Boolean(phraseErrorMessage)}>
                    <TextInput
                        id="phrases-input"
                        labelText="Phrase"
                        placeholder="Type a phrase and press Enter"
                        bind:value={phraseInput}
                        invalid={Boolean(phraseErrorMessage)}
                        invalidText={phraseErrorMessage}
                        on:change={addPhrase}
                    />
                </div>

                <fieldset class="phrases-params__toggles" aria-label="Phrase options">
                    <Checkbox
                        id="phrases-case-sensitive"
                        labelText="Case sensitive"
                        bind:checked={caseSensitive}
                    />
                    <Checkbox
                        id="phrases-use-regex"
                        labelText="Use regular expressions"
                        bind:checked={useRegex}
                    />
                </fieldset>

                {#if phrases.length > 0}
                    <ul class="phrases-params__tags" aria-label="Active phrases">
                        {#each phrases as phrase (phrase)}
                            <li>
                                <Tag
                                    filter
                                    title={`Remove phrase ${phrase}`}
                                    on:close={() => {
                                        removePhrase(phrase);
                                    }}
                                >
                                    {phrase}
                                </Tag>
                            </li>
                        {/each}
                    </ul>
                {/if}

                {#if persistenceError}
                    <InlineNotification
                        kind="error"
                        title="Error"
                        subtitle={`Failed to save phrase settings: ${persistenceError}`}
                    />
                {/if}
            </div>
        {/snippet}
    </ResultGrid>
</MetricSection>

<style>
    .phrases-params {
        display: flex;
        flex-direction: column;
    }

    .phrases-params__add-row {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }

    :global(.phrases-params__add-row .bx--text-input__field-wrapper) {
        width: 100%;
    }

    .phrases-params__toggles {
        border: 0;
        display: flex;
        flex-wrap: wrap;
        margin: 0.75rem 0;
        padding: 0;
    }

    /* Reduce the natural margin appended by Carbon checkboxes to bring them closer together */
    :global(.phrases-params__toggles .bx--checkbox-wrapper) {
        margin-right: 1.5rem;
    }
    :global(.phrases-params__toggles .bx--checkbox-wrapper:first-of-type) {
        margin-top: 0;
    }

    .phrases-params__tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        list-style: none;
        margin: 0;
        padding: 0;
    }

    @media (max-width: 42rem) {
        .phrases-params__add-row {
            flex-direction: column;
            align-items: stretch;
        }
    }
</style>
