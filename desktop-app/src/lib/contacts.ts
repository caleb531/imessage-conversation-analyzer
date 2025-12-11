import { invoke } from "@tauri-apps/api/core";

export async function fetchContactNames(): Promise<string[]> {
  return invoke<string[]>("get_contact_names");
}
