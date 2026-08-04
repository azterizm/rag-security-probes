#!/usr/bin/env python3
"""Probe Export Utility — Memon Systems Ltd."""

import argparse
import json
import os
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS_FILE = REPO_ROOT / "rag_probes.jsonl"
GROUND_TRUTH_FILE = REPO_ROOT / "ground_truth.json"

def load_probes():
    probes = []
    with open(DATASETS_FILE, "r") as f:
        for line in f:
            if line.strip():
                probes.append(json.loads(line))
    return probes

def load_ground_truth():
    with open(GROUND_TRUTH_FILE, "r") as f:
        gt = json.load(f)
    return {item["probe_id"]: item for item in gt}

def export_promptfoo(probes, ground_truth, out_dir, endpoint_placeholder):
    tests = []
    for p in probes:
        pid = p["probe_id"]
        gt = ground_truth.get(pid, {})
        asserts = []
        for contain in gt.get("must_contain", []):
            asserts.append({"type": "contains", "value": contain})
        for not_contain in gt.get("must_not_contain", []):
            asserts.append({"type": "not-contains", "value": not_contain})
            
        tests.append({
            "description": f"{pid}: {p['family']} / {p['class']}",
            "vars": {
                "query": p["query"]
            },
            "assert": asserts
        })

    config = {
        "providers": [
            {
                "id": "rag-target",
                "config": {
                    "url": endpoint_placeholder,
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "query": "{{query}}"
                    }
                }
            }
        ],
        "tests": tests
    }

    out_file = out_dir / "promptfoo_config.yaml"
    with open(out_file, "w") as f:
        yaml.dump(config, f, sort_keys=False)
    print(f"Generated {out_file}")

def export_pytest(probes, ground_truth, out_dir):
    out_file = out_dir / "test_rag_probes.py"
    with open(out_file, "w") as f:
        f.write('import requests\nimport pytest\n\n')
        f.write('ENDPOINT_URL = "https://YOUR-RAG-ENDPOINT/v1/query"\n\n')
        for p in probes:
            pid = p["probe_id"]
            gt = ground_truth.get(pid, {})
            f.write(f'def test_{pid.replace("-", "_").lower()}():\n')
            f.write(f'    query = {repr(p["query"])}\n')
            f.write(f'    response = requests.post(ENDPOINT_URL, json={{"query": query}}, headers={{"Content-Type": "application/json"}})\n')
            f.write(f'    answer = response.json().get("answer", "")\n')
            for contain in gt.get("must_contain", []):
                f.write(f'    assert {repr(contain)} in answer\n')
            for not_contain in gt.get("must_not_contain", []):
                f.write(f'    assert {repr(not_contain)} not in answer\n')
            f.write('\n')
    print(f"Generated {out_file}")

def export_curl(probes, out_dir, endpoint_placeholder):
    out_file = out_dir / "run_probes.sh"
    with open(out_file, "w") as f:
        f.write('#!/usr/bin/env bash\n')
        f.write('# RAG Security Probes — Generated curl commands\n')
        f.write(f'ENDPOINT_URL="{endpoint_placeholder}"\n\n')
        for p in probes:
            pid = p["probe_id"]
            f.write(f'echo "=== {pid}: {p["family"]} / {p["class"]} ==="\n')
            f.write(f'curl -s -X POST "$ENDPOINT_URL" \\\n')
            f.write(f'  -H "Content-Type: application/json" \\\n')
            f.write(f'  -d {repr(json.dumps({"query": p["query"]}))} \\\n')
            f.write(f'  > {pid.lower().replace("-", "_")}_response.json\n')
            f.write(f'echo "Response saved to {pid.lower().replace("-", "_")}_response.json"\n')
            f.write('echo ""\n\n')
    
    os.chmod(out_file, 0o755)
    print(f"Generated {out_file}")

def export_manifest(probes, ground_truth, out_dir):
    out_file = out_dir / "probe_manifest.json"
    manifest = []
    for p in probes:
        pid = p["probe_id"]
        gt = ground_truth.get(pid, {})
        entry = {**p, "ground_truth": gt}
        manifest.append(entry)
        
    with open(out_file, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Generated {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Export RAG Security Probes")
    parser.add_argument("--format", choices=["promptfoo", "pytest", "curl", "manifest", "all"], required=True)
    parser.add_argument("--endpoint-placeholder", default="https://YOUR-RAG-ENDPOINT/v1/query")
    parser.add_argument("--output-dir", default="exports")
    
    args = parser.parse_args()
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)
    
    probes = load_probes()
    ground_truth = load_ground_truth()
    
    if args.format in ["promptfoo", "all"]:
        export_promptfoo(probes, ground_truth, out_dir, args.endpoint_placeholder)
    if args.format in ["pytest", "all"]:
        export_pytest(probes, ground_truth, out_dir)
    if args.format in ["curl", "all"]:
        export_curl(probes, out_dir, args.endpoint_placeholder)
    if args.format in ["manifest", "all"]:
        export_manifest(probes, ground_truth, out_dir)

if __name__ == "__main__":
    main()
