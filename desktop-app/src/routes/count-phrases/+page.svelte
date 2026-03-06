<script lang="ts">
    import { Button, Checkbox, Tag, TextInput } from 'carbon-components-svelte';
    import ResultGrid from '../../components/ResultGrid.svelte';

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

    // Adds a phrase on Enter while preventing the parent filter form from submitting.
    function onPhraseInputKeydown(event: KeyboardEvent) {
        if (event.key !== 'Enter') {
            return;
        }

        event.preventDefault();
        addPhrase();
    }
</script>

<ResultGrid
    title="Count Phrases"
    description="Count how often one or more custom phrases appear in your conversation."
    {command}
    isReady={isReadyToAnalyze}
    notReadyMessage="Add phrases to begin analysis."
>
    {#snippet parameters(isReloadingData)}
        <div class="count-phrases-params">
            <div class="count-phrases-params__add-row">
                <TextInput
                    id="count-phrases-input"
                    labelText="Phrase"
                    placeholder="Type a phrase and click Add"
                    bind:value={phraseInput}
                    disabled={isReloadingData}
                    invalid={Boolean(phraseErrorMessage)}
                    invalidText={phraseErrorMessage}
                    on:keydown={onPhraseInputKeydown}
                />
                <div class="count-phrases-params__add-button-wrapper">
                    <Button
                        kind="secondary"
                        size="small"
                        type="button"
                        disabled={isReloadingData ||
                            (!canAddPhrase &&
                                phrases.includes(phraseInput.trim()) === false &&
                                phraseInput.trim() !== '')}
                        onclick={addPhrase}
                    >
                        Add
                    </Button>
                </div>
            </div>

            <div class="count-phrases-params__toggles" aria-label="Phrase options">
                <Checkbox
                    id="count-phrases-case-sensitive"
                    labelText="Case sensitive"
                    bind:checked={caseSensitive}
                    disabled={isReloadingData}
                />
                <Checkbox
                    id="count-phrases-use-regex"
                    labelText="Use regular expressions"
                    bind:checked={useRegex}
                    disabled={isReloadingData}
                />
            </div>

            {#if phrases.length > 0}
                <div class="count-phrases-params__tags" aria-label="Active phrases">
                    {#each phrases as phrase (phrase)}
                        <Tag
                            filter
                            title={`Remove phrase ${phrase}`}
                            disabled={isReloadingData}
                            on:close={() => {
                                removePhrase(phrase);
                            }}
                        >
                            {phrase}
                        </Tag>
                    {/each}
                </div>
            {/if}
        </div>
    {/snippet}
</ResultGrid>

<style>
    .count-phrases-params {
        width: min(100%, 52rem);
        display: flex;
        flex-direction: column;
    }

    .count-phrases-params__add-row {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }

    :global(.count-phrases-params__add-row .bx--text-input__field-wrapper) {
        width: 100%;
    }

    .count-phrases-params__add-button-wrapper {
        margin-top: 24px;
    }

    .count-phrases-params__toggles {
        display: flex;
        flex-wrap: wrap;
        margin-bottom: 0.75rem;
    }

    /* Reduce the natural margin appended by Carbon checkboxes to bring them closer together */
    :global(.count-phrases-params__toggles .bx--checkbox-wrapper) {
        margin-right: 1.5rem;
    }

    .count-phrases-params__tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    @media (max-width: 42rem) {
        .count-phrases-params__add-row {
            flex-direction: column;
            align-items: stretch;
        }

        .count-phrases-params__add-button-wrapper {
            margin-top: 0;
        }
    }
</style>
