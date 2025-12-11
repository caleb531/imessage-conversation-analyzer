<script lang="ts">
  import { onMount } from "svelte";
  import { Button, Combobox } from "bits-ui";
  import { fetchContactNames } from "../lib/contacts";
  import { runIcaSidecar } from "../lib/sidecar";
  import "../styles/page.css";
  import "../styles/combobox.css";

  let icaArgs = $state("--help");
  let icaOutput = $state("");
  let icaError = $state("");
  let icaRunning = $state(false);
  let contactNames = $state<string[]>([]);
  let contactsLoading = $state(true);
  let contactsError = $state("");
  let selectedContact = $state<string | undefined>(undefined);
  let searchTerm = $state("");
  let comboboxItems = $state<{ value: string; label: string }[]>([]);
  let filteredItems = $state<{ value: string; label: string }[]>([]);
  let comboboxInputEl = $state<HTMLInputElement | null>(null);

  onMount(loadContacts);

  async function loadContacts() {
    contactsLoading = true;
    contactsError = "";
    try {
      const names = await fetchContactNames();
      contactNames = names;
      updateComboboxItems(names);
      updateFilteredItems();
      ensureSelection();
    } catch (error) {
      contactsError = error instanceof Error ? error.message : String(error);
      contactNames = [];
      updateComboboxItems([]);
      updateFilteredItems();
      ensureSelection();
    } finally {
      contactsLoading = false;
    }
  }

  function updateComboboxItems(names: string[]) {
    comboboxItems = names.map((name) => ({ value: name, label: name }));
  }

  function updateFilteredItems() {
    const query = searchTerm.trim().toLowerCase();
    if (!query) {
      filteredItems = comboboxItems.slice();
      return;
    }
    filteredItems = comboboxItems.filter((item) =>
      item.label.toLowerCase().includes(query)
    );
  }

  function ensureSelection() {
    const first = filteredItems[0];
    selectedContact = first ? first.value : undefined;
  }

  function handleInput(event: Event & { currentTarget: HTMLInputElement }) {
    comboboxInputEl = event.currentTarget;
    searchTerm = event.currentTarget.value;
    updateFilteredItems();
    ensureSelection();
  }

  function handleInputFocus(event: Event & { currentTarget: HTMLInputElement }) {
    comboboxInputEl = event.currentTarget;
  }

  function selectItem(item?: { value: string; label: string }) {
    if (!item) {
      return;
    }
    selectedContact = item.value;
    searchTerm = item.label;
     if (comboboxInputEl) {
       comboboxInputEl.value = item.label;
     }
    updateFilteredItems();
    ensureSelection();
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === "Enter") {
      comboboxInputEl = event.currentTarget as HTMLInputElement;
      event.preventDefault();
      selectItem(filteredItems[0]);
    }
  }

  function splitArgs(input: string): string[] {
    // Support very small subset of shell quoting for convenience in the UI.
    return (
      input
        .match(/(?:"[^"]*"|'[^']*'|\S+)/g)
        ?.map((token) => token.replace(/^['"]|['"]$/g, "")) ?? []
    );
  }

  async function runSidecar(event: Event) {
    event.preventDefault();
    icaRunning = true;
    icaOutput = "";
    icaError = "";
    try {
      const args = icaArgs.trim() ? splitArgs(icaArgs) : [];
      const result = await runIcaSidecar(args);
      icaOutput = result.stdout.trimEnd();
      icaError = result.stderr.trimEnd();
    } catch (error) {
      icaError = error instanceof Error ? error.message : String(error);
    } finally {
      icaRunning = false;
    }
  }
</script>

<h1>iMessage Conversation Analyzer</h1>
<section class="contacts-section" aria-labelledby="contacts-label">
  <h2 id="contacts-label">Choose a contact</h2>
  {#if contactsLoading}
    <p class="contact-status">Loading contacts…</p>
  {:else if contactsError}
    <p class="contact-status contact-status--error">{contactsError}</p>
    <button type="button" class="contact-retry" onclick={loadContacts}>
      Try again
    </button>
  {:else}
    <div class="contact-combobox__container">
      <Combobox.Root
        type="single"
        bind:value={selectedContact}
        items={comboboxItems}
        disabled={!comboboxItems.length}
      >
        <div class="contact-combobox__field">
          <Combobox.Input
            class="contact-combobox__input"
            placeholder="Search contacts…"
            aria-label="Search contacts"
            onfocus={handleInputFocus}
            oninput={handleInput}
            onkeydown={handleKeyDown}
          />
          <Combobox.Trigger
            class="contact-combobox__trigger"
            aria-label="Toggle contacts menu"
          >
            <span aria-hidden="true">▾</span>
          </Combobox.Trigger>
        </div>
        <Combobox.Portal>
          <Combobox.Content class="contact-combobox__content" sideOffset={6}>
            <Combobox.Viewport class="contact-combobox__viewport">
              {#if filteredItems.length}
                {#each filteredItems as item (item.value)}
                  <Combobox.Item
                    class="contact-combobox__item"
                    value={item.value}
                    label={item.label}
                    onclick={() => selectItem(item)}
                  >
                    {#snippet children({ selected })}
                      <span>{item.label}</span>
                      {#if selected}
                        <span class="contact-combobox__check" aria-hidden="true">✓</span>
                      {/if}
                    {/snippet}
                  </Combobox.Item>
                {/each}
              {:else}
                <span class="contact-combobox__empty">No contacts available</span>
              {/if}
            </Combobox.Viewport>
          </Combobox.Content>
        </Combobox.Portal>
      </Combobox.Root>
    </div>
    {#if !comboboxItems.length}
      <p class="contact-status contact-status--empty">No contacts are available.</p>
    {/if}
    {#if selectedContact}
      <p class="contact-status contact-status--selection">
        Selected contact: {selectedContact}
      </p>
    {/if}
  {/if}
</section>
<form class="column" onsubmit={runSidecar}>
  <label for="sidecar-args">CLI Arguments</label>
  <input
    id="sidecar-args"
    placeholder="--help"
    bind:value={icaArgs}
    autocomplete="off"
  />
  <Button.Root type="submit" disabled={icaRunning}>
    {icaRunning ? "Running…" : "Run ica-sidecar"}
  </Button.Root>
</form>

{#if icaOutput}
  <pre>{icaOutput}</pre>
{/if}

{#if icaError}
  <pre class="error-log">{icaError}</pre>
{/if}
