# UK Golden RAG Security Probes

*Published by [Memon Systems Ltd](https://memonsystems.com)*

UK Golden RAG Security Probes is a collection of high-fidelity, UK-specific probe datasets designed to test security and isolation boundaries in Retrieval-Augmented Generation (RAG) pipelines. These probes test whether a RAG deployment maintains data isolation between tenants, resists prompt injection overrides, correctly disambiguates UK statutes, and correctly honors point-in-time constraints. This battery is designed for internal testing and self-service diagnostics on synthetic RAG deployments.

The full suite of active probes, along with their testing criteria and parameters, can be viewed directly in [rag_probes.csv](rag_probes.csv) or mechanically parsed from [rag_probes.jsonl](rag_probes.jsonl).

## Getting Started

1. **Hydrate the Corpora & Validate**  
   Run the unified build command to expand document boilerplate, validate schemas, and generate CSV companions:
   ```bash
   python scripts/prepare.py
   ```
2. **Ingest the Datasets**  
   Upload the documents in `.hydrated_synthetic_corpora.yaml` into your target RAG system.

## Integrating with Your Pipeline

Rather than running manual tests, use our export tool to generate ready-to-run configurations for your preferred framework:

```bash
# Generate Promptfoo configuration
python scripts/export_probes.py --format promptfoo --endpoint-placeholder "https://YOUR-RAG-ENDPOINT/v1/query"

# Generate pytest configuration
python scripts/export_probes.py --format pytest

# Generate raw curl script
python scripts/export_probes.py --format curl --endpoint-placeholder "https://YOUR-RAG-ENDPOINT/v1/query"

# Export all formats to a specific directory
python scripts/export_probes.py --format all --output-dir exports/
```
Once generated, simply fill in your endpoint URL and run your framework.

## Published Limits

- **Injection probes** measure instruction-boundary override via token emission, **not** data exfiltration.
- **Results** characterise pipeline architecture on synthetic documents, **not** the vendor's production index at scale.
- **Passing this general battery** proves baseline architectural properties; it does **not** establish domain-specific accuracy on practice areas.

> **Legal Boundary Policy:**
> - **Self-Service Usage:** The published probe datasets contain instruction injection payloads and cross-tenant canary tests designed for vendor internal dev/staging environments.
> - **Testing Restrictions:** Firing these probes against third-party SaaS trial accounts without written authorization violates SaaS Terms of Service and constitutes an offense under the **Computer Misuse Act 1990**.
> - **Outreach Line:** When contacting prospects, Memon Systems Ltd uses *only* ordinary-use probes (citation checks, non-determinism diffs) on public trials, while linking to this published dataset as standing methodology.

For the full, domain-specific paid diagnostic, visit [Memon Systems Ltd](https://memonsystems.com).
