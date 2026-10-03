# Temporal-protiah classifier

The matcher examines every adjacent candidate independently of the old
`_temporal_end` admission rule. Stanza proposes dependencies; the grammar uses
all relevant VESUM readings for case, adjective agreement and numeral government.
A viable nominative, accusative, indeclinable or quantity alternative blocks a
firm verdict. Parser disagreement, unsupported scope and missing morphology
remain suspicions. An independently attested accusative duration can establish
a draught reading when the tree also proposes duration; that reading emits no
book finding. Unknown draught readings remain suspicions.

## Provisioning and provenance

Use the project interpreter to run:

```sh
.venv/bin/python -m scripts.verification.provision_stanza_uk --help
.venv/bin/python -m scripts.verification.provision_stanza_uk
.venv/bin/python -m scripts.verification.provision_stanza_uk --verify-only
```

Use the task-prescribed absolute shared interpreter in dispatch worktrees.
This is the only model installer. It retrieves the immutable Hugging Face
revision in `stanza_uk_manifest.json`, checks lengths and SHA-256 before staging
and installation, and supplies deterministic resources metadata for the shared
Stanza consumers. No weights belong in Git. `STANZA_RESOURCES_DIR` can select the
installation root; otherwise it is `~/stanza_resources/protiah/<revision>`.
Processor and dependency file paths always come from the tracked inventory.
Nightly CI points its existing Stanza consumers at that same installation.

Stanza remains 1.13.0. The chosen upstream weights are the 1.13.0 model release;
newer lemma checkpoints are incompatible. Runtime downloads are disabled, and
all required bytes and resources metadata are verified once before loading.
Evidence includes the exact model revision. See
[third-party notices](../third-party/STANZA_UK_NOTICES.md).

## Budgets and failure behavior

`scripts/verification/temporal_protiah.py` sets four Torch threads, a 20-second
cold cap (including a synthetic candidate warmup), a 100 ms per-sentence cap,
a 500 ms cumulative inference budget per `check_text` call and a 40-token
sentence limit. These bounds are fixed; callers cannot override them through
the public checker. Cold initialization has its own cap. Repeated candidate
occurrences in one sentence share a parsed tree. The call budget spans items.

The parser subprocess starts only on a candidate, loads once and runs under
one nonblocking lock. Lock contention never queues. Deadline expiry terminates
the child and latches unavailable for that server process; later candidates
remain suspicions until the server process restarts. Optional imports stay
inside candidate-triggered initialization. No parser or Torch import occurs
at server startup or on candidate-free calls. Every infrastructure failure
carries `parser_unavailable: true` with a bounded reason code.

Per-occurrence status and grammatical reason participate in public finding
grouping, preserving equal surface forms with different dispositions. Original
input offsets and the book's p131 provenance remain attached.

## Certification and development

`FIRM_ENABLED = False` in `temporal_protiah.py` is the firm-capable grammar gate.
`TEMPORAL_PROTIAH_STATUS = "suspicion"` in `antonenko_patterns.py` is the fallback
status. Neither transport success nor a green test enables firm findings.

`tests/verification/protiah_development.json` contains 24 author-labelled
examples, two temporal and two draught examples in each of six classes. They
are development evidence, not independent evaluation. All 45 distinct forms
were attested through VESUM; attestation does not certify sentence syntax.
Fast tests use injected trees for logic and exercise real loader/supervisor
failure seams. The `slow` test runs the real model repeatedly and invokes the
unchanged 600-token, under-two-second warm benchmark with weights loaded.
Real-model determinism is tested separately from the production deadline: a
slow but valid model must still return suspicion through the bounded adapter.

Measure fresh-load elapsed time and RSS before/after weights plus warmup in a
fresh interpreter. Measure 72 native inference calls (three per development
sentence), reporting nearest-rank p95, thread configuration and model revision.
Run the original `test_speed_warm_call_under_2s` with the loaded model, then the
standalone `bench_check_text` benchmark. Report bounded firm recall separately
from diagnostic grammar recall obtained with a real parser without deadlines;
the latter cannot establish admission or product performance.

The driver freezes the code SHA, grammar, model manifest digest and configuration
and runs its independently frozen set once. The implementer does not access
that set. Any false positive, insufficient recall, missing proof or latency
failure retains suspicion. A second held-out attempt needs a newly written
independent set. After two development/review rounds, stop on material new
failure classes and hand the residual to the driver; do not lower the bar.
