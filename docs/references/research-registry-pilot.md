# ADR-011 Research Registry P6 Pilot

## Decision

**GO for a controlled local rollout with explicit task-scoped context or a known
functional role.** Generic and genuinely role-unknown startup remains silent:
`MonitorClient().bootstrap()` has no hidden default role and receives no research
pointers. New research ingestion remains schema- and adoption-gated. The compiled
default remains disabled; the gitignored local live flag is the local opt-in.

Rollback is immediate: set that live flag to `false` or remove it. No source
revert, task-store rewrite, or telemetry deletion is required.

## Method

`scripts/audit/check_research_registry_pilot.py` uses the three committed UNLP
records in `docs/references/research-registry.yaml`; it does not create synthetic
records. It builds each filtered payload with the production canonical JSON
serializer, measures `len(payload_bytes)`, and compares explicit expected sets.
It also uses an isolated FastAPI `TestClient` harness with a frozen manifest time
and response telemetry disabled. The harness sets the registry flag only in its
own process and restores all changed process state afterwards.
`tests/test_research_registry_p6.py` invokes this checker, so the existing pytest
CI path keeps these invariants durable without a separate workflow.

The checker protects the production caps from `scripts.research.registry`:
filtered pointers are at most 1,536 bytes, a record body at most 4,096 bytes, the
research manifest component at most 512 bytes, and the whole state manifest under
2,048 bytes. It has no dependency on mutable consumption telemetry or task state.

## Five-case discovery result

| Context | Expected record IDs | Serialized UTF-8 bytes |
| --- | --- | ---: |
| quality · difficulty-gate · core · `scripts/audit/text_difficulty.py` | `unlp-2026-cefr-assessment` | 342 |
| tts · tts · `scripts/tts/**` | `unlp-2025-stress-tts` | 251 |
| reviewer · reviewer-prompt · `agents_extensions/**` | `unlp-2026-gec-minimal-edit` | 280 |
| unrelated UI | none | 29 |
| unrelated CI | none | 29 |

The explicit-set confusion matrix is **TP 3, FP 0, FN 0**: precision is
`3 / (3 + 0) = 1.0` and recall is `3 / (3 + 0) = 1.0`. The zero-result controls
are measured responses, not denominator exclusions.

## Byte and warm-cache measurements

| Surface | Exact serialized UTF-8 bytes |
| --- | ---: |
| CEFR record body | 2,630 |
| TTS record body | 2,629 |
| GEC record body | 3,483 |
| State-manifest `research` component | 107 |
| State manifest, registry disabled | 912 |
| State manifest, registry enabled | 1,031 |
| Enabled-minus-disabled manifest delta | 119 |

The API proof is end-to-end, not a helper-only check:

- quality filtered manifest: `200 / 342`, then `304 / 0`;
- CEFR record body: `200 / 2630`, then `304 / 0`;
- a UI context offered the quality ETag returns its own `200 / 29` before its
  own repeat returns `304 / 0`. Context A therefore cannot borrow context B's
  ETag.

## P4 lifecycle, adoption, and live evidence

The ordinary registry check and strict-adoption gate both passed against a freshly
refreshed authoritative membership cache. The monitor is deliberately ungated and
reports only safe aggregate lifecycle and consumption fields. At the measured
full-coverage 30-day monitor sample, lifecycle was 3 total records: 1 adopted,
2 deferred, 0 stale, 0 orphaned, 0 superseded, and 0 invalid. Effective adoption
was 1 of 3 (0.3333); dead consumers were 0. Discovery status was enabled for this
local operational measurement.

The separate live surfaced-to-consumed measurement was complete (`partial:
false`): 1 surfaced pair, 1 consumed pair, 2 consumed events, 0 pending, and
0 surfaced-but-never-consumed pairs. The sole observed record ID was
`unlp-2026-cefr-assessment`. This report intentionally excludes task IDs, event
rows, prompts, paths, source contents, and raw telemetry.

## P5 disposition and limits

**NO-GO / condition not triggered.** All three bounded digests are sufficient;
CEFR adoption shipped without raw transport; and deferred TTS/GEC work remains
blocked by ownership, product, and licensing constraints. P5 may reopen only
when all of these are evidenced: a specific missing datum, a blocked routed task,
proof that the digest and public/manual access are insufficient, repeated need,
and rights that permit automated caching.

The pilot does not claim that keyword/path routing is semantic retrieval, that a
single local measurement predicts every environment, or that a pointer is a
consumption. The strict registry gate and the monitor remain the checks for
future lifecycle/adoption rot.
