#!/usr/bin/env python3
"""Single Build Entry Point — Memon Systems Ltd."""

import subprocess
from pathlib import Path
import json

REPO_ROOT = Path(__file__).resolve().parent.parent

def run_script(script_name: str) -> bool:
    script_path = REPO_ROOT / "scripts" / script_name
    result = subprocess.run(["python3", str(script_path)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}:\n{result.stderr}")
        return False
    print(result.stdout)
    return True

def cross_ref_check() -> bool:
    print("[4/4] Cross-reference check...")
    probes = []
    with open(REPO_ROOT / "rag_probes.jsonl") as f:
        for line in f:
            if line.strip():
                probes.append(json.loads(line))
    
    with open(REPO_ROOT / "ground_truth.json") as f:
        gt = json.load(f)
        
    probe_ids = {p["probe_id"] for p in probes}
    gt_ids = {g["probe_id"] for g in gt}
    
    if probe_ids == gt_ids:
        print(f"  ✓ All {len(probe_ids)} probe IDs matched between dataset and ground truth")
        print("\n═══════════════════════════════════════════════════════════")
        print(f"  UK RAG Security Probes — Ready")
        print(f"  Total: {len(probe_ids)} probes")
        print(f"  Hydrated corpora: .hydrated_synthetic_corpora.yaml")
        print("═══════════════════════════════════════════════════════════\n")
        return True
    else:
        print(f"  ✗ Mismatch! Probes missing from GT: {probe_ids - gt_ids}")
        print(f"  ✗ Mismatch! GT missing from probes: {gt_ids - probe_ids}")
        return False

def main():
    print("[1/4] Hydrating corpora...")
    if not run_script("hydrate_corpora.py"): return
    
    print("[2/4] Validating schemas...")
    if not run_script("validate_dataset.py"): return
    
    print("[3/4] Generating CSV companions...")
    if not run_script("jsonl_to_csv.py"): return
    
    cross_ref_check()

if __name__ == "__main__":
    main()
