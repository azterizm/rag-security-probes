# Contributor Guide: Adding New Probes

This guide outlines the standard workflow for enriching the **RAG Security Probes** repository with new tests. 

Always follow the pipeline: **Corpora → JSONL → Ground Truth → Validate**.

## 1. Update Corpora (`corpora/*.yaml`)
If your test requires new documents, plant them in the synthetic corpora. 
*   **Example:** Add a new trap document to `synthetic_tenant_a.yaml`.
*   **Note:** If you need a new deterministic canary token, generate one via:
    ```bash
    python3 scripts/generate_invariants.py --seed "your-seed"
    ```

## 2. Add the Probe Dataset (`datasets/*.jsonl`)
Append your query to the relevant `.jsonl` file as a single line of JSON. 
*   **Requirements:** Must include `probe_id`, `family`, `class`, `tier`, `evaluator`, `query`, and `tenant_context`.
*   **Example:** A new prompt injection test goes into `datasets/injection_resistance.jsonl`.

## 3. Define Ground Truth (`ground_truth/*.json`)
Append the expected passing/failing criteria to the matching ground truth array.
*   **Requirements:** The `probe_id` must match exactly.
*   **Example:** Add a `must_not_contain` rule to `ground_truth/injection_truth.json` to ensure the model doesn't output your injected payload.

## 4. Run Validations
Validate your manual entries against the strict JSON schemas to catch typos or missing fields:
```bash
python3 scripts/validate_dataset.py
```
*(Proceed only when this returns `[OK]` for all files).*

## 5. Generate CSV Companions
**Never hand-edit the CSV files.** They are strictly auto-generated for GitHub rendering. 
Update them automatically from your newly added JSONL data:
```bash
python3 scripts/jsonl_to_csv.py
```

## 6. Commit
Once validation passes and CSVs are generated, commit and push your changes!
