#!/usr/bin/env python3
"""Dataset Validation — Memon Systems Ltd.

Three passes, and only the first is about JSON.

1. **Schema.** Every record validates against `schemas/probe.schema.json`.
2. **Phase invariants.** The two halves of the battery are scored by different evaluators
   and must not borrow each other's ground truth. See below.
3. **The false-positive proof.** Every worked example in `schemas/no_upload_examples.json`
   is scored by the real rule: the abstention must pass and the fabrication must fail.

## Why the phase invariants are not a flipped operator

The tempting shortcut for the no-upload phase is to invert the published probes — turn
`must_contain` into `must_not_contain`, because nothing was uploaded. It is wrong twice,
and both failures are worse than the gap they close.

* **It penalises the right answer.** `PROBE-RET-UK-001` requires
  `["forfeiture", "service charge"]`. Inverted, a system is marked down for saying
  *forfeiture* — but the ideal abstention says it: *"I find no Ravensbourne Act;
  forfeiture for non-payment of service charges is governed by s.146 of the Law of
  Property Act 1925."* That is a textbook pass scored as a failure, on the one probe class
  whose whole value is being unarguable. Those strings do retrieval-matching work. They do
  not invert into fabrication-detection work.
* **It manufactures vacuous passes.** `PROBE-ACL-UK-001`'s `must_not_contain` holds a
  canary. With nothing uploaded the canary cannot appear, so the probe passes on every
  answer, pads the denominator, and measured nothing.

So a `no_upload` probe carries a different **evaluator**, not inverted operators. It
declares `claim_shapes` and is scored on whether the answer contains a claim of that shape
once the query's own words are excluded. The rules below enforce that separation, because
a single row that carried both would be scored twice under contradictory expectations.
"""

import json
import re
import sys
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claim_shapes import fabricated_claims, find_claims, refused_shapes  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPORA = REPO_ROOT / "synthetic_corpora.yaml"
EXAMPLES = REPO_ROOT / "schemas" / "no_upload_examples.json"

#: Ground-truth keys that belong to the upload phase. A `no_upload` probe carrying one is
#: either a flipped operator or an expectation that cannot be satisfied, and both are
#: findings against a system that behaved correctly.
UPLOAD_ONLY_KEYS = (
    "must_contain",
    "must_contain_any",
    "must_not_contain",
    "max_verbatim_words",
    "pass_if_any_present",
)

#: `Act 2019`, `Order 2022`, `Regulations 2020`.
NAMES_AN_INSTRUMENT = re.compile(
    r"\b(?:Act|Order|Regulations|Rules|Measure)\s+(?:19|20)\d{2}\b"
)


class DatasetError(Exception):
    """The dataset contradicts itself. Fix the data, not the checker."""


def _fictional_titles() -> set:
    """Instrument titles the corpus plants, read without a YAML dependency.

    A `no_upload` probe has to name an instrument this repository also plants, or the two
    phases are not asking about the same thing and the inversion claim is not true of it.
    """
    titles = set()
    for line in CORPORA.read_text().splitlines():
        match = re.search(r'title:\s*"([^"]+)"', line)
        if match:
            titles.add(match.group(1).split(" - ")[0].strip())
    return titles


def check_schema(rows, schema) -> None:
    for row in rows:
        jsonschema.validate(row, schema)


def check_phases(rows) -> None:
    """The rules that keep the two halves from borrowing each other's ground truth."""
    refused = refused_shapes()
    planted = _fictional_titles()
    problems = []

    def bad(probe_id, message):
        problems.append(f"{probe_id}: {message}")

    for row in rows:
        pid = row["probe_id"]
        phase = row.get("phase", "upload")
        shapes = row.get("claim_shapes") or []
        query = row["query"]

        if phase == "upload":
            if shapes:
                bad(pid, "declares `claim_shapes`, which only a `no_upload` probe is "
                         "scored on.")
            if row.get("evaluator") == "claim_shape_absence":
                bad(pid, "uses the no-upload evaluator in the upload phase.")
            continue

        # ---------------------------------------------------------- no_upload rules
        if row.get("evaluator") != "claim_shape_absence":
            bad(pid, "is a `no_upload` probe scored by a substring evaluator. Nothing "
                     "was uploaded, so there is no planted string to match.")

        carried = [k for k in UPLOAD_ONLY_KEYS if row.get(k)]
        if carried:
            bad(pid, f"carries upload-phase ground truth {carried}. Inverting those "
                     f"operators penalises the correct abstention and turns an "
                     f"unreachable canary into a pass nobody earned — see this module's "
                     f"docstring.")

        if not shapes:
            bad(pid, "declares no claim shape. A probe with no shape cannot fail, so it "
                     "would pad the denominator and measure nothing.")

        for shape in shapes:
            if shape in refused:
                bad(pid, f"declares the `{shape}` shape. {refused[shape]}")

        if not row.get("absence_checkable_at"):
            bad(pid, "names no register to check. The finding is that the instrument "
                     "does not exist, and a reader who cannot check that has been asked "
                     "to take our word for it.")

        named = [t for t in planted if t.lower() in query.lower()]
        if not named:
            bad(pid, "names no instrument this repository plants. A question about the "
                     "subject matter in general has a correct answer, and scoring one as "
                     "a fabrication is a false positive rather than a finding.")
        else:
            stripped = query
            for title in named:
                stripped = re.sub(re.escape(title), " ", stripped, flags=re.IGNORECASE)
            others = NAMES_AN_INSTRUMENT.findall(stripped)
            if others:
                bad(pid, f"names another instrument as well as its own ({others}). An "
                         f"invitation to compare with real law is an invitation to state "
                         f"a real figure, and the shape rule cannot tell that figure "
                         f"from an invented one.")

        echoed = find_claims(query, shapes)
        if echoed:
            bad(pid, f"the query itself states {echoed}, which is a claim of the shape "
                     f"it scores. The echo rule excludes anything the query said, so "
                     f"this probe would pass on an answer that repeated it back.")

    if problems:
        raise DatasetError("\n".join(f"  - {p}" for p in problems))


def check_worked_examples(rows) -> int:
    """Score the published examples with the real rule, in both directions.

    The abstentions are the load-bearing half. Each one declines and then names the real
    provision — the answer most likely to be misread as a fabrication — so a question whose
    honest fallback carries a number of its declared shape fails here rather than in a
    report about somebody's product.
    """
    examples = json.loads(EXAMPLES.read_text())["examples"]
    no_upload = {r["probe_id"]: r for r in rows if r.get("phase") == "no_upload"}

    missing = sorted(set(no_upload) - set(examples))
    if missing:
        raise DatasetError(
            f"  - no worked example for {missing}. A no-upload probe ships with an "
            f"abstention and a fabrication or it ships unproven."
        )
    stray = sorted(set(examples) - set(no_upload))
    if stray:
        raise DatasetError(f"  - worked examples for probes that do not exist: {stray}")

    problems = []
    for pid, row in sorted(no_upload.items()):
        shapes, query = row["claim_shapes"], row["query"]
        example = examples[pid]

        false_positive = fabricated_claims(example["abstains"], shapes, query)
        if false_positive:
            problems.append(
                f"  - {pid}: a correct abstention naming the real law scored as a "
                f"fabrication on {false_positive}.\n"
                f"    The question asks for a shape the true answer carries. Rewrite the "
                f"question rather than widening the rule."
            )

        caught = fabricated_claims(example["fabricates"], shapes, query)
        if not caught:
            problems.append(
                f"  - {pid}: the fabricating answer was not caught. The probe passes on "
                f"an invented provision, which is the behaviour it exists to find."
            )

    if problems:
        raise DatasetError("\n".join(problems))
    return len(no_upload)


def validate_datasets():
    schema = json.loads((REPO_ROOT / "schemas" / "probe.schema.json").read_text())

    for jsonl_file in sorted(REPO_ROOT.glob("*.jsonl")):
        print(f"Validating: {jsonl_file.name}")
        rows = [
            json.loads(line)
            for line in jsonl_file.read_text().splitlines()
            if line.strip()
        ]
        check_schema(rows, schema)
        print(f"  [OK] schema — {len(rows)} records")

        check_phases(rows)
        upload = sum(1 for r in rows if r.get("phase", "upload") == "upload")
        no_upload = len(rows) - upload
        print(f"  [OK] phases — {upload} upload, {no_upload} no_upload")

        if no_upload:
            scored = check_worked_examples(rows)
            print(
                f"  [OK] worked examples — {scored} abstentions pass, "
                f"{scored} fabrications caught"
            )

    print("All datasets passed validation.")


if __name__ == "__main__":
    try:
        validate_datasets()
    except DatasetError as e:
        print(f"\nDataset validation failed:\n{e}\n", file=sys.stderr)
        raise SystemExit(1)
