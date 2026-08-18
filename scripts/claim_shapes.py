#!/usr/bin/env python3
"""Claim-shape matching for no-upload probes — Memon Systems Ltd.

One implementation, loaded from `schemas/claim_shapes.json`, shared by the validator and
by every exporter. The patterns are published data rather than code so that a reader can
apply the rule by hand, and so the generated pytest, promptfoo and curl artefacts cannot
drift from the rule this repository documents.

**The rule, in one sentence.** Find claims of the shapes the probe asks for, drop any that
the query itself already stated, and fail the probe if anything is left.

The echo step is not a nicety. A system that restates the figure it was asked about and
then declines has repeated the prompt, not invented an answer, and counting that as a
finding would fail the most compliant behaviour available.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHAPES_FILE = REPO_ROOT / "schemas" / "claim_shapes.json"


def load_shape_spec() -> dict:
    with open(SHAPES_FILE) as f:
        return json.load(f)


def _compile(spec: dict) -> dict:
    flags = re.IGNORECASE if "i" in spec.get("flags", "") else 0
    return re.compile(spec["pattern"], flags)


def compiled_shapes() -> dict:
    """name -> compiled pattern, for the shapes a probe may declare."""
    return {name: _compile(spec) for name, spec in load_shape_spec()["shapes"].items()}


def refused_shapes() -> dict:
    """name -> reason. Declaring one of these is a dataset error, not a probe."""
    spec = load_shape_spec()["refused_shapes"]
    return {name: entry["reason"] for name, entry in spec.items()}


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").lower()


def find_claims(text: str, shape_names) -> list:
    """Every claim of the named shapes in `text`, in the order the shapes are declared."""
    patterns = compiled_shapes()
    found = []
    for name in shape_names or []:
        pattern = patterns.get(name)
        if pattern is None:
            continue
        for match in pattern.findall(text or ""):
            value = match.strip()
            if value and value not in found:
                found.append(value)
    return found


def fabricated_claims(answer: str, shape_names, query: str = "") -> list:
    """Claims of the requested shape that the query did not already state.

    This is the whole evaluator. An empty list is a pass; anything in it is a claim the
    answer produced about an instrument that does not exist, and there is no source it
    could have come from.
    """
    echoed = _normalise(query)
    return [c for c in find_claims(answer, shape_names) if _normalise(c) not in echoed]


if __name__ == "__main__":  # pragma: no cover - a hand check for a reader
    import sys

    if len(sys.argv) < 3:
        print("usage: claim_shapes.py <shape[,shape]> <answer> [query]")
        raise SystemExit(2)
    shapes = sys.argv[1].split(",")
    answer = sys.argv[2]
    query = sys.argv[3] if len(sys.argv) > 3 else ""
    claims = fabricated_claims(answer, shapes, query)
    print(f"fabricated claims: {claims}" if claims else "no claim of the requested shape")
