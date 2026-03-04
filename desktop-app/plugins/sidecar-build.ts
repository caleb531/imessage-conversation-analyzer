import { execa } from 'execa';
import { resolve } from 'node:path';
import type { Plugin } from 'vite';

// Creates a deduplicated sidecar build runner so concurrent hooks share one build promise.
function createSidecarBuildRunner() {
    // In-flight build promise used to serialize repeated build triggers.
    let buildPromise: Promise<void> | undefined;
    // Workspace root used as cwd and for script resolution.
    const projectRoot = process.cwd();
    // Absolute path to the sidecar build script.
    const scriptPath = resolve(projectRoot, 'scripts', 'build-sidecar.sh');

    // Runs the sidecar build script once and reuses the same promise while running.
    async function runBuild() {
        if (!buildPromise) {
            const runPromise = (async () => {
                await execa(scriptPath, {
                    cwd: projectRoot,
                    stdio: 'inherit'
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

// Vite plugin that builds the Rust/CLI sidecar before dev serve and production builds.
export function sidecarBuildPlugin(): Plugin {
    // Shared build runner reused by both configureServer and buildStart hooks.
    const runBuild = createSidecarBuildRunner();
    // Captures whether Vite is currently running in `serve` or `build` mode.
    let viteCommand: 'serve' | 'build' | undefined;
    // Tracks whether serve mode has already performed its initial build.
    let builtForServe = false;
    // Tracks whether build mode has already performed its sidecar build.
    let builtForBuild = false;

    return {
        name: 'ica-sidecar-build',
        enforce: 'pre',
        configResolved(config) {
            // Persist Vite's top-level command so each hook can decide whether
            // it should trigger the sidecar build.
            viteCommand = config.command;
        },
        async configureServer() {
            // Only run in actual dev server mode and only once per process.
            if (viteCommand !== 'serve' || builtForServe) {
                return;
            }
            await runBuild();
            builtForServe = true;
        },
        async buildStart(options) {
            // Rollup passes normalized input options; `watch` indicates watch mode.
            const isWatchMode = Boolean((options as { watch?: unknown }).watch);
            // Skip buildStart-triggered rebuilds during dev/watch mode because
            // configureServer already handles the serve startup build.
            if (viteCommand === 'serve' || isWatchMode) {
                return;
            }

            // In production builds, run once per process even if buildStart
            // is triggered more than once by the toolchain.
            if (builtForBuild) {
                return;
            }

            await runBuild();
            builtForBuild = true;
        }
    };
}

export default sidecarBuildPlugin;
