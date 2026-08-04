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

def main():
    print("[1/3] Hydrating corpora...")
    if not run_script("hydrate_corpora.py"): return
    
    print("[2/3] Validating schemas...")
    if not run_script("validate_dataset.py"): return
    
    print("[3/3] Generating CSV companions...")
    if not run_script("jsonl_to_csv.py"): return

    print("\n═══════════════════════════════════════════════════════════")
    print("  UK RAG Security Probes — Ready")
    print("  Hydrated corpora: .hydrated_synthetic_corpora.yaml")
    print("═══════════════════════════════════════════════════════════\n")

if __name__ == "__main__":
    main()
