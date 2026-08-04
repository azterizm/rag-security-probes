#!/usr/bin/env python3
"""JSONL to CSV Companion Generator — Memon Systems Ltd."""

import csv, json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

for jsonl_file in REPO_ROOT.glob("*.jsonl"):
    csv_file = jsonl_file.with_suffix(".csv")
    rows = []
    with open(jsonl_file) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    if not rows:
        continue
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {jsonl_file.name} -> {csv_file.name}")
