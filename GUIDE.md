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
*   **Ground truth:** `must_contain`, `must_contain_any`, `must_not_contain`, `max_verbatim_words` (as applicable)
*   Must validate against `schemas/probe.schema.json`.

## 3. Run the Prepare Script
**Never hand-edit the CSV files.** They are strictly auto-generated for GitHub rendering. 
Once you have made your changes, run the single build command to hydrate corpora, validate schemas, and generate CSVs:

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
