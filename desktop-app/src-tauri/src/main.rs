// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

/// Binary entrypoint that delegates startup to the shared Tauri library crate.
fn main() {
    imessage_conversation_analyzer_lib::run()
}
