#!/usr/bin/env python3
"""Single Build Entry Point — Memon Systems Ltd."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def run_script(script_name: str) -> bool:
    script_path = REPO_ROOT / "scripts" / script_name
    result = subprocess.run(["python3", str(script_path)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}:\n{result.stderr}")
        return False
    print(result.stdout)
    return True

def main() -> int:
    """Returns an exit code. A build step that fails must fail the build.

    The validator now holds a false-positive gate: it scores a published abstention
    against every no-upload probe and refuses the dataset if a correct answer would be
    recorded as a fabrication. A gate whose caller exits 0 either way is not a gate.
    """
    print("[1/4] Hydrating corpora...")
    if not run_script("hydrate_corpora.py"): return 1

    print("[2/4] Validating schemas, phases and worked examples...")
    if not run_script("validate_dataset.py"): return 1

    print("[3/4] Checking the generated exports apply the published rule...")
    if not run_script("check_exports.py"): return 1

    print("[4/4] Generating CSV companions...")
    if not run_script("jsonl_to_csv.py"): return 1

    print("\n═══════════════════════════════════════════════════════════")
    print("  UK RAG Security Probes — Ready")
    print("  Hydrated corpora: .hydrated_synthetic_corpora.yaml")
    print("═══════════════════════════════════════════════════════════\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
