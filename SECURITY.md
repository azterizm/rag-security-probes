# Security and Scope

The `upload` phase runs against a corpus you upload to a system you control. Ingesting synthetic documents and querying them is ordinary product use.

The `no_upload` phase uploads nothing. It is six typed questions about instruments that are on no public register, asked before any ingestion — no corpus, no second tenant, no payload, no automation beyond sending a question and reading the answer. It is the lightest-touch half of the battery by a wide margin, and it is the half that still works when you have no ingestion access at all.

**Order matters, and it is not a preference.** Run every `no_upload` probe before you ingest the corpus. The ground truth is that the instrument is absent from the index; ingest it and you have planted the very Act the probe says does not exist, so the question then scores retrieval and the fabrication finding is gone.

Handling requirements attach to the probe family, not to individual probes. Families are enumerated in [`schemas/probe.schema.json`](schemas/probe.schema.json).

| Family | Requirement |
|---|---|
| `cross_tenant_leakage` | Two tenants under your control. A positive result against a system you do not own means you have retrieved another party's data. |
| `injection_resistance` | The payload is embedded in corpus you supply. It targets your own instruction boundary, not vendor infrastructure. |
| `hallucination_abstention` (`no_upload` phase) | Nothing is uploaded and nothing is planted. A question typed into the product, and the answer read. |
| Mode C (`phase: "mode_c"`) | Run against an index populated with real UK legislation. Tests whether the pipeline rejects false premises or sycophantically misattributes authority. |
| All other families | Ordinary retrieval queries against your own corpus. |

Run against staging or a dedicated test tenant. Never a production index.

Some providers restrict security testing, benchmarking, or publication of results in their terms. Check before testing a system you do not own.

If a `cross_tenant_leakage` probe returns real data on a system you do not own, stop and report it to the provider.
