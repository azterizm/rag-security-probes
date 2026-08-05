#!/usr/bin/env python3
"""Probe Export Utility — Memon Systems Ltd."""

import argparse
import json
import os
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROBES_FILE = REPO_ROOT / "rag_probes.jsonl"

GENERAL_BANNER = """# ⚠️  SECURITY PROBES — AUTHORIZATION WARNING
# This battery contains injection payloads and cross-tenant canary tests.
# Ensure you have explicit authorization before running against third-party systems.
# See README.md Legal Boundary Policy.

"""

def load_probes():
    probes = []
    with open(PROBES_FILE, "r") as f:
        for line in f:
            if line.strip():
                probes.append(json.loads(line))
    return probes

def export_promptfoo(probes, out_dir, endpoint_placeholder):
    tests = []
    for p in probes:
        pid = p["probe_id"]
        asserts = []
        for contain in p.get("must_contain", []):
            asserts.append({"type": "icontains", "value": contain})
        for contain_any in p.get("must_contain_any", []):
            js_conds = [f"output.toLowerCase().includes({json.dumps(s.lower())})" for s in contain_any]
            asserts.append({
                "type": "javascript",
                "value": " || ".join(js_conds)
            })
        for not_contain in p.get("must_not_contain", []):
            asserts.append({"type": "not-icontains", "value": not_contain})
        if p.get("pass_if_any_present"):
            flat_list = [s for sublist in p["pass_if_any_present"] for s in sublist]
            js_conds = [f"output.toLowerCase().includes({json.dumps(s.lower())})" for s in flat_list]
            asserts.append({
                "type": "javascript",
                "value": " || ".join(js_conds)
            })
            
        tests.append({
            "description": f"{pid}: {p['family']} / {p['class']}",
            "vars": {
                "query": p["query"],
                "tenant_id": p.get("issuing_tenant_id", "default")
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
                        "Content-Type": "application/json",
                        "X-Tenant-ID": "{{tenant_id}}"
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

def export_pytest(probes, out_dir):
    out_file = out_dir / "test_rag_probes.py"
    with open(out_file, "w") as f:
        f.write(GENERAL_BANNER)
        f.write('import requests\nimport pytest\n\n')
        f.write('ENDPOINT_URL = "https://YOUR-RAG-ENDPOINT/v1/query"\n\n')
        for p in probes:
            pid = p["probe_id"]
            f.write(f'def test_{pid.replace("-", "_").lower()}():\n')
            f.write(f'    query = {repr(p["query"])}\n')
            f.write(f'    response = requests.post(ENDPOINT_URL, json={{"query": query}}, headers={{"Content-Type": "application/json", "X-Tenant-ID": "{p.get("issuing_tenant_id", "default")}"}})\n')
            f.write(f'    answer = response.json().get("answer", "")\n')
            f.write(f'    answer_lower = answer.lower()\n')
            for contain in p.get("must_contain", []):
                f.write(f'    assert {repr(contain.lower())} in answer_lower\n')
            if p.get("must_contain_any"):
                any_list = [repr(s.lower()) for s in p["must_contain_any"]]
                f.write(f'    assert any(s in answer_lower for s in [{", ".join(any_list)}])\n')
            for not_contain in p.get("must_not_contain", []):
                f.write(f'    assert {repr(not_contain.lower())} not in answer_lower\n')
            if p.get("pass_if_any_present"):
                flat_list = [repr(s.lower()) for sublist in p["pass_if_any_present"] for s in sublist]
                f.write(f'    assert any(s in answer_lower for s in [{", ".join(flat_list)}])\n')
            f.write('\n')
    print(f"Generated {out_file}")

def export_curl(probes, out_dir, endpoint_placeholder):
    out_file = out_dir / "run_probes.sh"
    with open(out_file, "w") as f:
        f.write('#!/usr/bin/env bash\n')
        f.write(GENERAL_BANNER)
        f.write(f'ENDPOINT_URL="{endpoint_placeholder}"\n\n')
        for p in probes:
            pid = p["probe_id"]
            f.write(f'echo "=== {pid}: {p["family"]} / {p["class"]} ==="\n')
            f.write(f'curl -s -X POST "$ENDPOINT_URL" \\\n')
            f.write(f'  -H "Content-Type: application/json" \\\n')
            f.write(f'  -H "X-Tenant-ID: {p.get("issuing_tenant_id", "default")}" \\\n')
            f.write(f'  -d {repr(json.dumps({"query": p["query"]}))} \\\n')
            f.write(f'  > {pid.lower().replace("-", "_")}_response.json\n')
            f.write(f'echo "Response saved to {pid.lower().replace("-", "_")}_response.json"\n')
            f.write('echo ""\n\n')
    os.chmod(out_file, 0o755)
    print(f"Generated {out_file}")

def export_manifest(probes, out_dir):
    out_file = out_dir / "probe_manifest.json"
    with open(out_file, "w") as f:
        json.dump(probes, f, indent=2)
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
    
    if args.format in ["promptfoo", "all"]:
        export_promptfoo(probes, out_dir, args.endpoint_placeholder)
    if args.format in ["pytest", "all"]:
        export_pytest(probes, out_dir)
    if args.format in ["curl", "all"]:
        export_curl(probes, out_dir, args.endpoint_placeholder)
    if args.format in ["manifest", "all"]:
        export_manifest(probes, out_dir)

if __name__ == "__main__":
    main()
