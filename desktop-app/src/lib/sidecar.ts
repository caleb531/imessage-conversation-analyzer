import { Command } from "@tauri-apps/plugin-shell";

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
  const command = Command.sidecar("ica-sidecar", args);
  return command.execute();
}
