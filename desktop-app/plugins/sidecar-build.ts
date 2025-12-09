import { execa } from "execa";
import { resolve } from "node:path";
import type { Plugin } from "vite";

type BuildStartContext = {
  meta?: {
    watchMode?: boolean;
  };
};

function createSidecarBuildRunner() {
  let buildPromise: Promise<void> | undefined;
  const projectRoot = process.cwd();
  const scriptPath = resolve(projectRoot, "scripts", "build-sidecar.sh");
  const tauriDebugRuntime = resolve(
    projectRoot,
    "src-tauri",
    "target",
    "debug",
    "_internal",
  );
  const tauriReleaseRuntime = resolve(
    projectRoot,
    "src-tauri",
    "target",
    "release",
    "_internal",
  );

  async function runBuild() {
    if (!buildPromise) {
      const runPromise = (async () => {
        await execa(scriptPath, {
          cwd: projectRoot,
          stdio: "inherit",
        });
      })();

      buildPromise = runPromise.finally(() => {
        buildPromise = undefined;
      });
    }

    await buildPromise;
  }

  return runBuild;
}

export function sidecarBuildPlugin(): Plugin {
  const runBuild = createSidecarBuildRunner();
  let builtForServe = false;

  return {
    name: "ica-sidecar-build",
    enforce: "pre",
    async configureServer() {
      if (builtForServe) {
        return;
      }
      await runBuild();
      builtForServe = true;
    },
    async buildStart(this: BuildStartContext) {
      if (this.meta?.watchMode && builtForServe) {
        return;
      }
      await runBuild();
    },
  };
}

export default sidecarBuildPlugin;
