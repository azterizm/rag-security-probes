#!/usr/bin/env python3
"""Seed-Based Invariant Generator — Memon Systems Ltd."""

import argparse, hmac, hashlib

def generate_canary(seed: str, plant_id: str) -> str:
    token = hmac.new(seed.encode(), plant_id.encode(), hashlib.sha256).hexdigest()[:8]
    return f"MSL-CANARY-{token.upper()}"

def main():
    parser = argparse.ArgumentParser(description="Generate deterministic RAG test invariants.")
    parser.add_argument("--seed", required=True)
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()
    for i in range(1, args.count + 1):
        pid = f"PLANT-{i:03d}"
        print(f"  {pid} -> {generate_canary(args.seed, pid)}")

if __name__ == "__main__":
    main()
