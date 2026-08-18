#!/usr/bin/env python3
"""Export Fidelity Check — Memon Systems Ltd.

The no-upload rule is published once, in `schemas/claim_shapes.json`, and then re-emitted
three times: into the generated pytest file, into the promptfoo assertion, and into
whatever a reader applies by hand. Three copies of a rule is three chances for one of them
to drift, and a drifted copy does not announce itself — it quietly scores somebody's
product by a rule this repository does not document.

So the generated artefacts are scored against the canonical matcher on the worked examples
in `schemas/no_upload_examples.json`, and the build fails if any of them disagrees.

The JavaScript half needs `node`. Where it is absent the check says so and skips that half
rather than passing silently, because a skipped check and a passing one must not read the
same way.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claim_shapes import fabricated_claims as canonical  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def _probes() -> dict:
    return {
        json.loads(line)["probe_id"]: json.loads(line)
        for line in (REPO_ROOT / "rag_probes.jsonl").read_text().splitlines()
        if line.strip()
    }


def _examples() -> dict:
    path = REPO_ROOT / "schemas" / "no_upload_examples.json"
    return json.loads(path.read_text())["examples"]


def _cases():
    """(probe, example answer, whether it should pass) for both directions."""
    probes, examples = _probes(), _examples()
    for pid, example in sorted(examples.items()):
        for kind, should_pass in (("abstains", True), ("fabricates", False)):
            yield probes[pid], pid, kind, example[kind], should_pass


def check_pytest(out_dir: Path) -> list:
    """The generated helper must agree with the canonical matcher, claim for claim."""
    source = (out_dir / "test_rag_probes.py").read_text()
    header = source.split("ENDPOINT_URL =")[0].replace(
        "import requests\nimport pytest\n", ""
    )
    namespace = {}
    exec(compile(header, "<generated pytest>", "exec"), namespace)  # nosec B102
    generated = namespace["fabricated_claims"]

    problems = []
    for probe, pid, kind, answer, should_pass in _cases():
        shapes, query = probe["claim_shapes"], probe["query"]
        theirs = generated(answer, shapes, query)
        ours = canonical(answer, shapes, query)
        if theirs != ours:
            problems.append(
                f"  - pytest/{pid}/{kind}: generated helper found {theirs}, the "
                f"published rule finds {ours}"
            )
        elif bool(theirs) is should_pass:
            problems.append(
                f"  - pytest/{pid}/{kind}: scored the wrong way ({theirs})"
            )
    return problems


def check_promptfoo(out_dir: Path) -> list:
    """The promptfoo assertion, executed by the engine that will actually run it."""
    config = yaml.safe_load((out_dir / "promptfoo_config.yaml").read_text())
    by_probe = {t["description"].split(":")[0]: t for t in config["tests"]}

    cases = []
    for probe, pid, kind, answer, should_pass in _cases():
        test = by_probe[pid]
        cases.append({
            "pid": pid,
            "kind": kind,
            "js": next(a["value"] for a in test["assert"] if a["type"] == "javascript"),
            "output": answer,
            "query": probe["query"],
            "shouldPass": should_pass,
        })

    script = (
        "const CASES = " + json.dumps(cases, ensure_ascii=False) + ";\n"
        "const bad = [];\n"
        "for (const c of CASES) {\n"
        "  const context = { vars: { query: c.query } };\n"
        "  const output = c.output;\n"
        "  const r = eval(c.js);\n"
        "  if (r.pass !== c.shouldPass) bad.push(`  - promptfoo/${c.pid}/${c.kind}: "
        "pass=${r.pass}, expected ${c.shouldPass} (${r.reason})`);\n"
        "}\n"
        "console.log(bad.join('\\n'));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(script)
        path = handle.name
    try:
        result = subprocess.run(
            ["node", path], capture_output=True, text=True, timeout=60
        )
    finally:
        Path(path).unlink(missing_ok=True)

    if result.returncode != 0:
        return [f"  - promptfoo: the assertion did not run under node:\n{result.stderr}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    probes = _probes()
    if not any(p.get("phase") == "no_upload" for p in probes.values()):
        print("  [SKIP] no no_upload probes to check")
        return 0

    out_dir = Path(tempfile.mkdtemp(prefix="probe-exports-"))
    try:
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "export_probes.py"),
             "--format", "all", "--output-dir", str(out_dir)],
            check=True, capture_output=True, text=True,
        )
        problems = check_pytest(out_dir)
        print("  [OK] pytest export applies the published rule")

        if shutil.which("node"):
            js_problems = check_promptfoo(out_dir)
            problems += js_problems
            if not js_problems:
                print("  [OK] promptfoo assertion applies the published rule")
        else:
            print("  [SKIP] promptfoo assertion not executed — `node` is not installed")
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)

    if problems:
        print("\nExport fidelity check failed:", file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        return 1

    print("Generated artefacts agree with schemas/claim_shapes.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
