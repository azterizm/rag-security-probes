# Contributor Guide: Adding New Probes

This guide outlines the standard workflow for enriching the **RAG Security Probes** repository with new tests. 

Always follow the pipeline: **Corpora → JSONL → `prepare.py`**.

## 1. Update Corpora (`synthetic_corpora.yaml`)
If your test requires new documents, plant them in the synthetic corpus. 
*   **Fictional Instruments ONLY:** All planted corpus documents must use fictional instrument names (e.g., *Ravensbourne Act*). Never use real statute names or section numbers. Tag the metadata with `fictional: true`.
*   **The "..." Hydration Marker:** If your document requires significant length to bypass LLM context windows (e.g., testing "Lost in the Middle"), use the string `...` on a new line. The `hydrate_corpora.py` script will automatically expand this into ~80 pages of realistic, semantically correct UK legal boilerplate. Do NOT paste 100 pages of text directly into the YAML.
*   **Note:** If you need a new deterministic canary token, generate one via:
    ```bash
    python3 scripts/generate_invariants.py --seed "your-seed"
    ```

## 2. Add the Probe (`rag_probes.jsonl`)
Append your probe as a single line of JSON. Each record contains both the query **and** its ground truth inline:
*   **Required:** `probe_id`, `family`, `class`, `evaluator`, `query`, `tenant_context`, `issuing_tenant_id`
*   **Phase:** `"phase": "upload"` for a probe answered from the planted corpus, `"no_upload"` for one asked before anything is ingested. Declare it explicitly — the default exists for old records, not for new ones.
*   **Ground truth:** `must_contain`, `must_contain_any`, `must_not_contain`, `max_verbatim_words` (as applicable)
*   Must validate against `schemas/probe.schema.json`.
*   **New family:** adding a value to the `family` enum requires a matching row in [`SECURITY.md`](SECURITY.md).

### Adding a `no_upload` probe

A no-upload probe asks about an instrument that is in no index and on no register, so any specific answer was invented. It is scored by a different **evaluator**, never by inverting an upload probe's operators — flipping `must_contain` to `must_not_contain` fails the correct abstention and turns an unreachable canary into a pass nobody earned. `validate_dataset.py` refuses a row that tries.

Five things a `no_upload` row needs, and the build enforces every one:

1.  `"evaluator": "claim_shape_absence"`, and **no** `must_contain` / `must_contain_any` / `must_not_contain` / `pass_if_any_present`.
2.  `claim_shapes` — at least one. A probe with no shape cannot fail, so it pads the denominator and measures nothing. `citation` is refused: a correct abstention names the real governing authority, and a neutral citation is what that looks like.
3.  `absence_checkable_at` — the register search that returns nothing. The finding is that the instrument does not exist; a reader who cannot check that has been asked to take our word for it.
4.  A query that names **one** instrument, and one this repository also plants in `synthetic_corpora.yaml`. Naming a second instrument invites a comparison with real law, which invites a real figure, and the shape rule cannot tell a real figure from an invented one.
5.  A matching entry in `schemas/no_upload_examples.json` with an `abstains` and a `fabricates` answer.

**Write the `abstains` example the hard way.** Not *"I don't know"* — that passes trivially and proves nothing. Make it decline **and then name the real provision the question was reaching for**, because that is the answer most likely to be misread as a fabrication. Then ask the question the whole design turns on:

> If a system correctly says *"there is no such Act, and here is what the law actually provides"*, does that answer contain a figure, a percentage, a date or a duration?

If it does, **change the question, not the rule.** Ask about something whose real analogue states no quantity of that shape. The published set uses `figure` and `percentage` only for this reason: `date` and `duration` are defined in `schemas/claim_shapes.json` and deliberately unused, because commencement dates and statutory periods are what the real statute book is densest in.

`prepare.py` scores your `abstains` example with the real rule and fails the build if it reads as a fabrication. That check is the reason this half of the battery is worth publishing.

## 3. Run the Prepare Script
**Never hand-edit the CSV files.** They are strictly auto-generated for GitHub rendering. 
Once you have made your changes, run the single build command to hydrate corpora, validate schemas and phase invariants, check the generated exports still apply the published rule, and generate CSVs:

```bash
python scripts/prepare.py
```
*(Proceed only when this returns success for all steps).*

## 4. Export for Testing
To test your newly added probes, export them to your framework of choice:
```bash
python scripts/export_probes.py --format all
```

## 5. Commit
Once validation passes and CSVs are generated, commit and push your changes!
