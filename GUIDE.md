# Contributor Guide: Adding New Probes

This guide outlines the standard workflow for enriching the **RAG Security Probes** repository with new tests. 

Always follow the pipeline: **Corpora → JSONL → Ground Truth → `prepare.py`**.

## 1. Update Corpora (`synthetic_corpora.yaml`)
If your test requires new documents, plant them in the synthetic corpus. 
*   **The "..." Hydration Marker:** If your document requires significant length to bypass LLM context windows (e.g., testing "Lost in the Middle"), use the string `...` on a new line. The `hydrate_corpora.py` script will automatically expand this into ~80 pages of realistic, semantically correct UK legal boilerplate. Do NOT paste 100 pages of text directly into the YAML.
*   **Note:** If you need a new deterministic canary token, generate one via:
    ```bash
    python3 scripts/generate_invariants.py --seed "your-seed"
    ```

## 2. Add the Probe Dataset (`rag_probes.jsonl`)
Append your query to the JSONL file as a single line of JSON. 
*   **Requirements:** Must include `probe_id`, `family`, `class`, `tier`, `evaluator`, `query`, and `tenant_context`. Make sure it validates against `schemas/probe.schema.json`.

## 3. Define Ground Truth (`ground_truth.json`)
Append the expected passing/failing criteria to the JSON array.
*   **Requirements:** The `probe_id` must match exactly. Specify `must_contain` and `must_not_contain` rules in flat format.

## 4. Run the Prepare Script
**Never hand-edit the CSV files.** They are strictly auto-generated for GitHub rendering. 
Once you have made your changes, run the single build command to hydrate corpora, validate schemas, generate CSVs, and cross-reference your probes:

```bash
python scripts/prepare.py
```
*(Proceed only when this returns success for all steps).*

## 5. Export for Testing
To test your newly added probes, export them to your framework of choice:
```bash
python scripts/export_probes.py --format all
```

## 6. Commit
Once validation passes and CSVs are generated, commit and push your changes!
