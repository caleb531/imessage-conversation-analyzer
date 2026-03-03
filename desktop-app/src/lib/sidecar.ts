import { Command } from "@tauri-apps/plugin-shell";

/** Result payload returned by the sidecar command execution. */
export interface SidecarResult {
  code: number | null;
  signal: number | null;
  stdout: string;
  stderr: string;
};

/**
 * Runs the packaged Python CLI as a Tauri sidecar and captures its output.
 */
export async function runIcaSidecar(args: string[] = []): Promise<SidecarResult> {
  try {
    const command = Command.sidecar("bin/ica-sidecar", args);
    return await command.execute();
  } catch (error) {
    throw new Error(`Failed to execute ICA sidecar (args: ${args.join(" ")}): ${String(error)}`, {
      cause: error
    });
  }
}
