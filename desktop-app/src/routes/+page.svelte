<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { runIcaSidecar } from "../lib/sidecar";

  let icaArgs = $state("--help");
  let icaOutput = $state("");
  let icaError = $state("");
  let icaRunning = $state(false);

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

<main class="container">
  <section class="section">
    <h1>iMessage Conversation Analyzer</h1>
    <form class="column" onsubmit={runSidecar}>
      <label for="sidecar-args">CLI Arguments</label>
      <input
        id="sidecar-args"
        placeholder="--help"
        bind:value={icaArgs}
        autocomplete="off"
      />
      <button type="submit" disabled={icaRunning}>
        {icaRunning ? "Running…" : "Run ica-sidecar"}
      </button>
    </form>

    {#if icaOutput}
      <pre>{icaOutput}</pre>
    {/if}

    {#if icaError}
      <pre class="error-log">{icaError}</pre>
    {/if}
  </section>
</main>

<style>
:root {
  font-family: Inter, Avenir, Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;

  color: #0f0f0f;
  background-color: #f6f6f6;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
}

.container {
  margin: 0;
  padding-top: 10vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
}

h1 {
  text-align: center;
}

input,
button {
  border-radius: 8px;
  border: 1px solid transparent;
  padding: 0.6em 1.2em;
  font-size: 1em;
  font-weight: 500;
  font-family: inherit;
  color: #0f0f0f;
  background-color: #ffffff;
  transition: border-color 0.25s;
  box-shadow: 0 2px 2px rgba(0, 0, 0, 0.2);
}

button {
  cursor: pointer;
}

button:hover {
  border-color: #396cd8;
}
button:active {
  border-color: #396cd8;
  background-color: #e8e8e8;
}

input,
button {
  outline: none;
}

.section {
  margin-top: 3rem;
}

pre {
  text-align: left;
  white-space: pre-wrap;
  word-break: break-word;
  background-color: #ffffff;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #d0d0d0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.error-log {
  color: #8b0000;
  background-color: #ffeeee;
  border-color: #ffb3b3;
}

@media (prefers-color-scheme: dark) {
  :root {
    color: #f6f6f6;
    background-color: #2f2f2f;
  }

  input,
  button {
    color: #ffffff;
    background-color: #0f0f0f98;
  }
  button:active {
    background-color: #0f0f0f69;
  }

  pre {
    background-color: #101010;
    border-color: #2b2b2b;
  }

  .error-log {
    color: #ffb3b3;
    background-color: #340101;
    border-color: #7a1e1e;
  }
}

</style>
