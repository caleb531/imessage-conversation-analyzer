import { Command } from "@tauri-apps/plugin-shell";

export type SidecarResult = {
  code: number;
  signal: string | null;
  stdout: string;
  stderr: string;
};

/**
 * Runs the packaged Python CLI as a Tauri sidecar and captures its output.
 */
export async function runIcaSidecar(args: string[] = []): Promise<SidecarResult> {
  const command = Command.sidecar("bin/ica-sidecar", args);
  const { code, signal, stdout, stderr } = await command.execute();
  return {
    code,
    signal,
    stdout,
    stderr,
  };
}
