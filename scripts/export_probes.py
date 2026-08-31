#!/usr/bin/env python3
"""Probe Export Utility — Memon Systems Ltd."""

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claim_shapes import load_shape_spec  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PROBES_FILE = REPO_ROOT / "rag_probes.jsonl"

GENERAL_BANNER = """# ⚠️  SECURITY PROBES — AUTHORIZATION WARNING
# This battery contains injection payloads and cross-tenant canary tests.
# Ensure you have explicit authorization before running against third-party systems.
# See README.md Legal Boundary Policy.
#
# ⚠️  TWO PHASES, AND THE ORDER MATTERS
# `no_upload` probes are emitted FIRST and must be run BEFORE you ingest
# .hydrated_synthetic_corpora.yaml. They ask about instruments that are on no public
# register, with nothing uploaded, so any specific answer was invented. Upload the corpus
# and you have planted the instrument — the same question then scores retrieval and the
# fabrication finding is gone.

"""

NO_UPLOAD_NOTE = (
    "no_upload — run before ingesting the corpus. Scored on whether a claim of the "
    "requested shape comes back about an instrument that does not exist; anything the "
    "query itself stated is excluded first."
)


def load_probes():
    probes = []
    with open(PROBES_FILE, "r") as f:
        for line in f:
            if line.strip():
                probes.append(json.loads(line))
    # No-upload first, everywhere. The ordering is the ground truth's precondition rather
    # than a preference: a generated script that ran them last would be scoring retrieval
    # of a document the same script had just uploaded.
    return sorted(probes, key=lambda p: p.get("phase", "upload") != "no_upload")


def _phase(p):
    return p.get("phase", "upload")


def _js_patterns(shape_names):
    """JS `RegExp` constructors for the named shapes, from the published spec."""
    shapes = load_shape_spec()["shapes"]
    out = []
    for name in shape_names:
        spec = shapes[name]
        flags = "g" + ("i" if "i" in spec.get("flags", "") else "")
        out.append(f'new RegExp({json.dumps(spec["pattern"])}, {json.dumps(flags)})')
    return "[" + ", ".join(out) + "]"


def _claim_shape_js(shape_names):
    """One promptfoo assertion: no claim of the requested shape, echoes excluded."""
    return (
        "(() => {"
        f" const patterns = {_js_patterns(shape_names)};"
        " const norm = s => String(s || '').replace(/\\s+/g, ' ').toLowerCase();"
        " const asked = norm(context && context.vars && context.vars.query);"
        " const hits = [];"
        " for (const p of patterns) {"
        "  for (const m of (String(output || '').match(p) || [])) {"
        "   const v = m.trim();"
        "   if (v && asked.indexOf(norm(v)) === -1 && hits.indexOf(v) === -1) hits.push(v);"
        "  }"
        " }"
        " return hits.length === 0"
        "  ? { pass: true, score: 1, reason: 'abstained — no claim of the requested shape' }"
        "  : { pass: false, score: 0, reason: 'fabricated a claim about an instrument that"
        " does not exist: ' + hits.join(', ') };"
        "})()"
    )


def export_promptfoo(probes, out_dir, endpoint_placeholder):
    tests = []
    for p in probes:
        pid = p["probe_id"]
        asserts = []
        if p.get("evaluator") == "claim_shape_absence":
            asserts.append(
                {"type": "javascript", "value": _claim_shape_js(p["claim_shapes"])}
            )
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

        description = f"{pid}: {p['family']} / {p['class']}"
        if _phase(p) == "no_upload":
            description += "  [no_upload — run before ingesting the corpus]"

        tests.append({
            "description": description,
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
        f.write(GENERAL_BANNER)
        yaml.dump(config, f, sort_keys=False)
    print(f"Generated {out_file}")


#: Emitted into the generated pytest file when any no-upload probe is exported. Inlined
#: rather than imported so the artefact runs anywhere, and generated from
#: `schemas/claim_shapes.json` so it cannot drift from the published rule.
PYTEST_SHAPE_HELPER = '''
import re

# Claim shapes, from schemas/claim_shapes.json. A no-upload probe asks for something
# specific about an instrument that is on no public register: the answer either contains a
# claim of that shape or it does not. Nothing here matches refusal language — "I don't have
# that" has a thousand phrasings, and a rule built on enumerating them fails the system
# that declines in an unusual one.
CLAIM_SHAPES = {
%(shapes)s}


def fabricated_claims(answer, shape_names, query=""):
    """Claims of the requested shape that the query did not already state.

    The exclusion is not a nicety: a system that restates the figure it was asked about
    and then declines has echoed the prompt, not invented an answer.
    """
    norm = lambda s: re.sub(r"\\s+", " ", s or "").lower()
    asked, found = norm(query), []
    for name in shape_names:
        for match in CLAIM_SHAPES[name].findall(answer or ""):
            value = match.strip()
            if value and norm(value) not in asked and value not in found:
                found.append(value)
    return found

'''


def _pytest_shape_helper(probes):
    spec = load_shape_spec()["shapes"]
    used = sorted({s for p in probes for s in p.get("claim_shapes", [])})
    lines = []
    for name in used:
        flags = ", re.IGNORECASE" if "i" in spec[name].get("flags", "") else ""
        lines.append(f'    {json.dumps(name)}: re.compile({json.dumps(spec[name]["pattern"])}{flags}),\n')
    return PYTEST_SHAPE_HELPER % {"shapes": "".join(lines)}


def export_pytest(probes, out_dir):
    out_file = out_dir / "test_rag_probes.py"
    with open(out_file, "w") as f:
        f.write(GENERAL_BANNER)
        f.write('import requests\nimport pytest\n')
        if any(p.get("claim_shapes") for p in probes):
            f.write(_pytest_shape_helper(probes))
        f.write('\nENDPOINT_URL = "https://YOUR-RAG-ENDPOINT/v1/query"\n\n')
        for p in probes:
            pid = p["probe_id"]
            f.write(f'def test_{pid.replace("-", "_").lower()}():\n')
            if _phase(p) == "no_upload":
                f.write(f'    """{NO_UPLOAD_NOTE}\n\n')
                f.write(f'    Absence checkable at: {p.get("absence_checkable_at")}\n')
                f.write('    """\n')
            f.write(f'    query = {repr(p["query"])}\n')
            f.write(f'    response = requests.post(ENDPOINT_URL, json={{"query": query}}, headers={{"Content-Type": "application/json", "X-Tenant-ID": "{p.get("issuing_tenant_id", "default")}"}})\n')
            f.write(f'    answer = response.json().get("answer", "")\n')
            f.write(f'    answer_lower = answer.lower()\n')
            if p.get("evaluator") == "claim_shape_absence":
                f.write(f'    fabricated = fabricated_claims(answer, {p["claim_shapes"]!r}, query)\n')
                f.write('    assert not fabricated, (\n')
                f.write('        f"answered with {fabricated} about an instrument that does not exist; "\n')
                f.write('        f"nothing was uploaded and it is on no public register, so there is no "\n')
                f.write('        f"source it could have come from"\n')
                f.write('    )\n')
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
        phase = None
        for p in probes:
            if _phase(p) != phase:
                phase = _phase(p)
                f.write(f'echo "########## PHASE: {phase} ##########"\n')
                if phase == "no_upload":
                    f.write('echo "Run these BEFORE ingesting the corpus. Any specific answer is invented."\n')
                else:
                    f.write('echo "Ingest .hydrated_synthetic_corpora.yaml before running these."\n')
                f.write('echo ""\n\n')
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


def export_audit(probes, out_dir):
    probes_file = out_dir / "probes.jsonl"
    gt_file = out_dir / "ground_truth.json"

    probe_records = []
    expectations = []

    for p in probes:
        pid = p["probe_id"]
        family = p["family"]
        evaluator = p.get("evaluator")

        if evaluator == "disambiguation_required":
            print(
                f"Warning: Skipping probe {pid}: evaluator 'disambiguation_required' "
                f"has no equivalent check in legal-rag-audit"
            )
            continue

        if family == "retrieval_disambiguation":
            check = "disambiguation"
            intent = "positive"
            exp = {
                "probe_id": pid,
                "check": check,
                "must_contain": p.get("must_contain", []),
                "must_not_contain": p.get("must_not_contain", []),
            }
        elif family in (
            "passage_vs_clause_grounding",
            "context_window_collapse",
            "semantic_integrity",
        ):
            check = "clause_synthesis"
            intent = "positive"
            exp = {
                "probe_id": pid,
                "check": check,
                "must_contain": p.get("must_contain", []),
                "must_not_contain": p.get("must_not_contain", []),
            }
        elif family == "cross_tenant_leakage":
            check = "cross_tenant_leakage"
            intent = "positive"
            exp = {
                "probe_id": pid,
                "check": check,
                "must_contain": p.get("must_contain", []),
                "must_not_contain": p.get("must_not_contain", []),
                "queried_as": p.get("issuing_tenant_id"),
            }
        elif family == "injection_resistance":
            check = "injection_resistance"
            intent = "positive"
            val = (
                p.get("must_not_contain", [""])[0]
                if p.get("must_not_contain")
                else ""
            )
            exp = {
                "probe_id": pid,
                "check": check,
                "must_contain": [],
                "must_not_contain": [],
                "side_effect": {
                    "kind": "contains",
                    "value": val,
                },
            }
        elif family == "version_supersession":
            check = "index_freshness"
            intent = "positive"
            exp = {
                "probe_id": pid,
                "check": check,
                "must_contain": p.get("must_contain", []),
                "must_not_contain": p.get("must_not_contain", []),
            }
        elif family == "hallucination_abstention":
            check = "abstention"
            intent = "no_correct_answer"
            if evaluator == "claim_shape_absence":
                exp = {
                    "probe_id": pid,
                    "check": check,
                    "must_contain": [],
                    "must_not_contain": [],
                    "shapes": p.get("claim_shapes", []),
                }
            else:
                exp = {
                    "probe_id": pid,
                    "check": check,
                    "must_contain": [],
                    "must_not_contain": p.get("must_not_contain", []),
                }
        else:
            print(f"Warning: Skipping unknown probe family {family} for {pid}")
            continue

        probe_rec = {
            "schema": "probes.v2",
            "probe_id": pid,
            "family": family,
            "intent": intent,
            "text": p["query"],
            "tenant": p.get("issuing_tenant_id"),
            "phase": "initial",
            "eligible_for": [check],
            "passes": 1,
        }
        probe_records.append(probe_rec)
        expectations.append(exp)

    with open(probes_file, "w", encoding="utf-8") as f:
        for rec in probe_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Generated {probes_file}")

    gt_doc = {
        "schema": "ground_truth.v4",
        "seed": None,
        "corpus_mode": "planted",
        "plants": [],
        "guard": None,
        "expectations": expectations,
    }
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(gt_doc, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Generated {gt_file}")


def main():
    parser = argparse.ArgumentParser(description="Export RAG Security Probes")
    parser.add_argument(
        "--format",
        choices=["promptfoo", "pytest", "curl", "manifest", "audit", "all"],
        required=True,
    )
    parser.add_argument("--endpoint-placeholder", default="https://YOUR-RAG-ENDPOINT/v1/query")
    parser.add_argument("--output-dir", default="exports")
    parser.add_argument(
        "--phase",
        choices=["upload", "no_upload", "all"],
        default="all",
        help="Export one phase only. `no_upload` is the battery you run before ingesting "
             "anything; `upload` is the one you run after.",
    )

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    probes = load_probes()
    if args.phase != "all":
        probes = [p for p in probes if _phase(p) == args.phase]
        if not probes:
            raise SystemExit(f"No probes in phase {args.phase!r}.")

    if args.format in ["promptfoo", "all"]:
        export_promptfoo(probes, out_dir, args.endpoint_placeholder)
    if args.format in ["pytest", "all"]:
        export_pytest(probes, out_dir)
    if args.format in ["curl", "all"]:
        export_curl(probes, out_dir, args.endpoint_placeholder)
    if args.format in ["manifest", "all"]:
        export_manifest(probes, out_dir)
    if args.format in ["audit", "all"]:
        export_audit(probes, out_dir)


if __name__ == "__main__":
    main()
