<script lang="ts">
  import { onMount } from "svelte";
  import { Button } from "bits-ui";
  import { runIcaSidecar } from "../lib/sidecar";
  import ContactPicker from "../components/ContactPicker.svelte";
  import "../styles/page.css";

  let icaArgs = $state("--help");
  let icaOutput = $state("");
  let icaError = $state("");
  let icaRunning = $state(false);
  let selectedContact = $state<string | undefined>(undefined);

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
  <ContactPicker bind:selectedContact />
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
