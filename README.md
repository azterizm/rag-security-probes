# RAG Security Probes

*Published by [Memon Systems Ltd](https://memonsystems.com)*

RAG Security Probes is a collection of high-fidelity, UK-specific probe datasets designed to test security and isolation boundaries in Retrieval-Augmented Generation (RAG) pipelines. These probes test whether a RAG deployment maintains data isolation between tenants, resists prompt injection overrides, correctly disambiguates UK statutes, and correctly honors point-in-time constraints. This battery is designed for internal testing and self-service diagnostics on synthetic RAG deployments.

The full suite of active probes, along with their testing criteria and parameters, can be viewed directly in [rag_probes.csv](rag_probes.csv) or mechanically parsed from [rag_probes.jsonl](rag_probes.jsonl).

## The Two Testing Modes

### Mode A: Fictional Corpus Battery
This published repository contains our **Mode A** battery. It relies on a planted corpus of purely **fictional** instruments (e.g., *Ravensbourne Commercial Tenancies Act 2019*). 
- **Collision-Proof**: No real legal index contains these Acts, eliminating conflicts with your system's pre-training or web-fetch capabilities.
- **Parametric Bleed Detection**: Any system confidently answering questions about these fictional Acts without relying on the planted corpus has fabricated its answer, providing an automatic hallucination finding.
- **Permanently Valid**: Fiction is not amended by Parliament, so ground truth never goes stale.

### Mode B: Live Legislation Validation
Testing against real UK law requires binding ground truth to `as_at_date` parameters and performing run-time revalidation against current legislation to manage statutory amendments. Because this methodology relies on active maintenance and continuous diffing against live parliamentary updates, it cannot be distributed as a static artifact. This dataset is maintained internally for direct engagements. Visit [Engagements page of Memon Systems Ltd](https://memonsystems.com/engagements) website for more information.

## Getting Started

1. **Hydrate the Corpora & Validate**  
   Run the unified build command to expand document boilerplate, validate schemas, and generate CSV companions:
   ```bash
   python scripts/prepare.py
   ```
2. **Ingest the Datasets**  
   Upload the fictional documents in `.hydrated_synthetic_corpora.yaml` into your target RAG system (staging or dedicated test tenant only).

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
> - This dataset contains active injection payloads and cross-tenant canary tests designed for vendor internal dev/staging environments.
> - Firing these probes against third-party SaaS trial accounts without written authorization violates SaaS Terms of Service and constitutes an offense under the **Computer Misuse Act 1990**.

For the full, domain-specific paid diagnostic, visit [Memon Systems Ltd](https://memonsystems.com/engagements).
