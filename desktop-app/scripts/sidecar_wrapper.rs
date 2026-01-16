use std::process::Command;
use std::env;
use std::os::unix::process::CommandExt;

fn main() {
    let exe = env::current_exe().expect("Failed to get current exe path");
    let dir = exe.parent().expect("Failed to get parent dir");

    // Path logic:
    // Prod (Bundle): contents/MacOS/wrapper -> contents/Resources/_internal...
    // Path: ../Resources/_internal/ica-sidecar/ica-sidecar
    // Dev: src-tauri/bin/wrapper -> src-tauri/_internal...
    // Path: ../../_internal/ica-sidecar/ica-sidecar

    let prod_path = dir.join("../Resources/_internal/ica-sidecar/ica-sidecar");
    let dev_path = dir.join("../../_internal/ica-sidecar/ica-sidecar");

    let target = if prod_path.exists() {
        prod_path
    } else if dev_path.exists() {
        dev_path
    } else {
        // Fallback: maybe we are in a weird location?
        eprintln!("Sidecar binary not found. Checked:");
        eprintln!("  {:?}", prod_path);
        eprintln!("  {:?}", dev_path);
        std::process::exit(1);
    };

    let args: Vec<String> = env::args().skip(1).collect();

    // Execute the target, replacing the current process
    let err = Command::new(target)
        .args(args)
        .exec();

    eprintln!("Failed to execute sidecar: {}", err);
    std::process::exit(1);
}
