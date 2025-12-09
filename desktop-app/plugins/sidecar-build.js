import { execa } from "execa";
import { resolve } from "node:path";

function createSidecarBuildRunner() {
  let buildPromise;

  async function runBuild() {
    if (!buildPromise) {
      const projectRoot = process.cwd();
      const scriptPath = resolve(projectRoot, "scripts", "build-sidecar.sh");
      buildPromise = execa(scriptPath, {
        cwd: projectRoot,
        stdio: "inherit",
      }).finally(() => {
        buildPromise = undefined;
      });
    }

    await buildPromise;
  }

  return runBuild;
}

export function sidecarBuildPlugin() {
  const runBuild = createSidecarBuildRunner();

  return {
    name: "ica-sidecar-build",
    enforce: "pre",
    async configureServer() {
      await runBuild();
    },
    async buildStart() {
      await runBuild();
    },
  };
}

export default sidecarBuildPlugin;
