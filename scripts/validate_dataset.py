#!/usr/bin/env python3
"""Dataset Validation — Memon Systems Ltd."""

import json
from pathlib import Path
import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent

def validate_datasets():
    with open(REPO_ROOT / "schemas" / "probe.schema.json") as f:
        probe_schema = json.load(f)

    for jsonl_file in REPO_ROOT.glob("*.jsonl"):
        print(f"Validating: {jsonl_file.name}")
        with open(jsonl_file) as f:
            for line in f:
                if line.strip():
                    jsonschema.validate(json.loads(line), probe_schema)
        print(f"  [OK] {jsonl_file.name}")

    print("All datasets passed schema validation.")

if __name__ == "__main__":
    validate_datasets()
