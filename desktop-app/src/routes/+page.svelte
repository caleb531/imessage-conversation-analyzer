<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { runIcaSidecar } from "../lib/sidecar";

  let name = $state("");
  let greetMsg = $state("");
  let sidecarArgs = $state("--help");
  let sidecarOutput = $state("");
  let sidecarError = $state("");
  let sidecarExitCode = $state<number | null>(null);
  let sidecarRunning = $state(false);

  async function greet(event: Event) {
    event.preventDefault();
    // Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
    greetMsg = await invoke("greet", { name });
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
    sidecarRunning = true;
    sidecarOutput = "";
    sidecarError = "";
    sidecarExitCode = null;

    try {
      const args = sidecarArgs.trim() ? splitArgs(sidecarArgs) : [];
      const result = await runIcaSidecar(args);
      sidecarExitCode = result.code;
      sidecarOutput = result.stdout.trimEnd();
      sidecarError = result.stderr.trimEnd();
    } catch (error) {
      sidecarExitCode = null;
      sidecarError = error instanceof Error ? error.message : String(error);
    } finally {
      sidecarRunning = false;
    }
  }
</script>

<main class="container">
  <h1>Welcome to Tauri + Svelte</h1>

  <div class="row">
    <a href="https://vite.dev" target="_blank">
      <img src="/vite.svg" class="logo vite" alt="Vite Logo" />
    </a>
    <a href="https://tauri.app" target="_blank">
      <img src="/tauri.svg" class="logo tauri" alt="Tauri Logo" />
    </a>
    <a href="https://svelte.dev" target="_blank">
      <img src="/svelte.svg" class="logo svelte-kit" alt="SvelteKit Logo" />
    </a>
  </div>
  <p>Click on the Tauri, Vite, and SvelteKit logos to learn more.</p>

  <form class="row" onsubmit={greet}>
    <input id="greet-input" placeholder="Enter a name..." bind:value={name} />
    <button type="submit">Greet</button>
  </form>
  <p>{greetMsg}</p>

  <section class="section">
    <h2>Run Packaged CLI</h2>
    <form class="column" onsubmit={runSidecar}>
      <label for="sidecar-args">Arguments</label>
      <input
        id="sidecar-args"
        placeholder="--help"
        bind:value={sidecarArgs}
        autocomplete="off"
      />
      <button type="submit" disabled={sidecarRunning}>
        {sidecarRunning ? "Running…" : "Run ica-sidecar"}
      </button>
    </form>

    {#if sidecarExitCode !== null}
      <p class="status">Exit code: {sidecarExitCode}</p>
    {/if}

    {#if sidecarOutput}
      <h3>Stdout</h3>
      <pre>{sidecarOutput}</pre>
    {/if}

    {#if sidecarError}
      <h3>Stderr</h3>
      <pre class="error-log">{sidecarError}</pre>
    {/if}
  </section>
</main>

<style>
.logo.vite:hover {
  filter: drop-shadow(0 0 2em #747bff);
}

.logo.svelte-kit:hover {
  filter: drop-shadow(0 0 2em #ff3e00);
}

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

.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: 0.75s;
}

.logo.tauri:hover {
  filter: drop-shadow(0 0 2em #24c8db);
}

.row {
  display: flex;
  justify-content: center;
}

.column {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.75rem;
  max-width: 30rem;
  margin: 0 auto;
}

a {
  font-weight: 500;
  color: #646cff;
  text-decoration: inherit;
}

a:hover {
  color: #535bf2;
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

#greet-input {
  margin-right: 5px;
}

.section {
  margin-top: 3rem;
}

.status {
  margin-top: 1rem;
  font-weight: 600;
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

  a:hover {
    color: #24c8db;
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
