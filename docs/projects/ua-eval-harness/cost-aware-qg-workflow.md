# Cost-Aware Curriculum QG Workflow

Issues: [#4310](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4310),
[#4311](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4311)

`scripts/audit/qg_workflow.py` composes the #4308 scorer adapters and the #4309
reviewer helpers into one canonical `ua_contact_quality_evidence.v1` record
per module. It is deliberately cost-aware: deterministic and lookup tiers run
first, and the LLM reviewer is never bulk-run by default.

## Tiers

| Tier | Source | Default behavior |
| --- | --- | --- |
| 0 | `DeterministicRuleAdapter` plus `run_structural_checks()` | Always runs. A hard `FAIL` short-circuits Tier 2 by default. |
| 1 | `UaGecGoldFixtureAdapter` | Cheap lookup. Dry-run reports `gold rows matched: N`, not "all modules hit Tier 1". |
| 2 | `llm_reviewer` prompt/parser | Eligible only for `policy_for_level(level).family` in `b1_plus` or `seminar`, or explicit `--force-llm` / calibration sample. |

The Tier-0 short-circuit intentionally overrides
`curriculum_qg_harness.llm_review.required` for cost. The harness still marks
non-`PASS` modules as LLM-required; this workflow skips the expensive tier on
hard deterministic failures unless `--llm-on-fail` or calibration sample mode
is used for richer diagnostics.

Seminar-family modules must be eligible for Tier 2 because factual,
decolonization, register, and living-subject risks are not fully covered by
Tier 0/1. Live Tier-2 dispatch is available only through
`--live-reviewer`; broad execution remains gated by dry-run approval, canaries,
budget rails, and explicit human spend sign-off.

## Live Dispatcher

`scripts/audit/llm_reviewer_dispatch.py` owns live reviewer routing:

- B1+ surface review routes to `ask-gemma` with
  `openrouter/google/gemma-4-31b-it` (surface/register review is prompt-only —
  no MCP requirement).
- Seminar, contested-gold, and factual-sensitive review routes to the tooled
  **`FRONTIER_OPENCODE_ROUTE`**: opencode transport with the **sources MCP**
  wired in, so factual/decolonization findings can be grounded (#2156, D0/D5).
  This replaces the old ungrounded `ask-agy --to-model gemini-3.1-pro-high`
  route, which an ungrounded reviewer could not use to catch the gemma
  fabrication class in `model-evidence.md`. The agy route stays **defined for
  fallback/reference** but is no longer returned by `route_for_review`. The
  frontier model is pinned to `openrouter/google/gemma-4-31b-it` until the
  step-3 bakeoff selects a frontier model (`openrouter/google/gemini-3.1-pro`
  is not yet reachable via `opencode models`).
- **MCP fail-fast:** before a grounded (frontier) opencode reviewer call the
  dispatcher verifies the `sources` MCP is configured + enabled in the ambient
  opencode config *and* that its endpoint (`http://127.0.0.1:8766/mcp`)
  responds. On failure it raises `ReviewerProviderError` — a grounded reviewer
  run must never silently proceed without tools.
- Each opencode reviewer run parses the NDJSON stream once for per-call
  telemetry; `DispatchResult` carries `tool_call_count` and `tools_used`, which
  the workflow persists to `llm_qg.db` (`tool_call_count`, `tools_used_json`).
- Escalation/disputed spot audit is Claude-only and is not the batch default.
- DeepSeek/Hermes reviewer routes are hard-banned for automated LLM-QG batches.

Live review also enforces cross-family lineage. The dispatcher resolves author
family from explicit `--author-family`, committed metadata, or git history. If
lineage is unavailable, the live call fails closed. If the reviewer family
matches the author family, the call is blocked as self-review; there is no
silent fallback to a same-family reviewer.

## Production factuality shadow run

`qg_shadow_run.py` captures one **fresh, live** Tier-2 review of a built folk
module, including the full learner-facing module, activities, vocabulary, and
resources surface. It does not invoke `qg_bakeoff` or create a fixture. The
capture is serialized as `qg_bakeoff_run.v2` only because that is the stable
replay artifact contract consumed by `layerb_shadow`.

The driver resolves real writer lineage before dispatch (explicit family,
module metadata, then git `X-Agent` history) and errors if it cannot do so.
It runs Layer B at the pinned `tau=0.75` only, writes a local audit artifact and
per-module Markdown evidence, then persists advisory rows in the separate
`llm_qg_shadow.db`. It neither reads nor writes canonical `llm_qg_runs`; Monitor
and build gating ignore the shadow database until an explicit cutover.

For a dry-ish end-to-end capture, use `--layerb-dry-run`: Tier 2 still runs, but
the tool-disabled judge does not. A judged invocation instead requires the
attested judge command, exact route identity, attestation, labels, and frozen
qualification manifests; `layerb_shadow` verifies all of them.

> [!WARNING]
> When minting the canary artifact for a seminar-level run, always run the canary generator with the specific target level (e.g. `folk` or `hist`), not the literal string `seminar`. Using `seminar` maps to the `b1_plus` policy family and `gemma_surface` route instead of `opencode_frontier`, which will fail validation.

```bash
.venv/bin/python scripts/audit/qg_shadow_run.py \
  --module-dir curriculum/l2-uk-en/folk/vesnianky-hayivky \
  --level folk \
  --author-family claude \
  --canary-artifact seminar=PATH_TO_PASSING_CANARY.json \
  --max-cost-usd 1.00 \
  --max-llm-calls 3 \
  --layerb-dry-run \
  --audit-dir audit/local-qg-shadow \
  --shadow-db data/telemetry/llm_qg_shadow.db
```

The resulting Markdown, replay artifact, Layer-B report, and local SQLite
database are operational evidence and must not be committed.

### Reviewer prompt compatibility contract

The Tier-2 reviewer prompt and emitted `fact_checks` remain compatible with the
attested factuality judge only when all of the following hold:

- A `CONFIRMED` or contradiction verdict has an actual captured
  `mcp__sources__*` call; model memory or an uncaptured citation never counts.
- Evidence excerpts are contiguous quotations from that tool output (a light
  ellipsis is permitted) and keep the source query visible. Paraphrase must
  never be presented as a quote.
- Keep the established shape: claim → tool reference → quoted excerpt →
  verdict. Do not invent a parallel verdict schema.
- Authors prefer claims supported by the indexed sources and retain opaque
  canonical `source_ref` keys. Claims outside that corpus go to human audit.
- The reviewer captures evidence and makes its own verdict; the separate,
  tool-disabled Layer-B judge audits grounding. Do not pre-judge grounding in
  the reviewer prompt.
- Shadow verdicts are advisory only until a separately approved cutover.

## Cost Controls

Use `--dry-run` before broad reviewer spend:

```bash
.venv/bin/python scripts/audit/qg_workflow.py \
  --target b1:aspect-in-imperatives:curriculum/l2-uk-en/b1/aspect-in-imperatives \
  --dry-run \
  --format json
```

Dry-run writes nothing. It reports per-tier module counts, Tier-1 gold-row
matches, and Tier-2 token/cost estimates bucketed by level-policy family. The
dry-run JSON also contains a gateable artifact with:

- exact module list and chosen reviewer route/model,
- per-tier counts,
- warm/cold/stale cache estimate,
- expected spend by reviewer model,
- stale-cache count,
- exact non-dry run command.

The current estimator uses prompt size with route-specific completion budgets.
Use `--calibrate --live-reviewer` on a small, approved probe set before trusting
broad frontier totals; calibration reports an observed/estimated cost factor.

Tier-2 budgets are checked before any reviewer call:

- `--max-llm-calls` is the primary per-run ceiling.
- `--max-cost-usd` caps the whole run and is required for live non-dry runs.
- `--max-daily-cost-usd` is a local safety rail persisted under
  `data/telemetry/`.
- `--max-module-cost-usd` blocks pathological prompts.

Budget exhaustion is explicit: the evidence carries
`workflow_verdict: SKIPPED_BUDGET` and `completion_status: INCOMPLETE`. Because
`qg_schema` only admits `PASS/WARN/FAIL`, incomplete LLM-required records stay
schema-valid by using top-level `verdict: FAIL` and `terminal_verdict: FAIL`
when fail-closed mode is active.

Any live Tier-2 call requires a passing dispatcher canary artifact for the same
level, gate version, prompt template hash, reviewer model, reviewer family, and
route. Mixed-level batches need one canary artifact per level family. Dry-run
does not need the canary because it does not call the reviewer.

The batch aborts and marks remaining records `INCOMPLETE` when any hard rail
fires: canary failure, self-review, parse/schema failure rate above 5%,
provider error rate above 10%, or observed cost above 125% of the estimate.

## Cache Key

The workflow reuses `scripts/audit/llm_qg_store.py`; it does not create a
parallel store. Current Tier-2 cache lookup is composite:

```text
content_sha
+ gate_version
+ prompt_hash
+ checker_version
+ level_policy.family
+ reviewer_model_id
+ route_name
```

`route_name` (#2156) joins the composite key so a transport change invalidates
ungrounded cache rows even when the reviewer model id is unchanged.

The canonical content basis is `llm_qg_store.CONTENT_FILES`:

```text
module.md, activities.yaml, vocabulary.yaml, resources.yaml
```

Plan YAML is intentionally not part of this workflow cache hash. This differs
from `scripts/build/promote_quality_gate.py`, whose promotion sidecar hashes
the plan plus learner files. Workflow evidence records document the chosen
basis under `qg_workflow.content_hash_basis` and
`qg_workflow.content_files`, so cache invalidation is auditable.

`gate_version` and `prompt_hash` must bump when #4370 changes reviewer
calibration; stale LLM evidence then misses the composite cache automatically.

`DEFAULT_GATE_VERSION` was bumped to **`qg_workflow.v2`** (#2156) when
seminar/factual moved onto the tooled opencode transport. Implication: every
pre-#2156 (ungrounded, v1) row in a local `data/telemetry/llm_qg.db` now misses
the composite cache and re-runs through the grounded route on the next
`--live-reviewer` pass. This is intended — v1 evidence was produced without
tools and must not be reused.

## Contested Gold

Tier 1 preserves #4364 contested-gold metadata. If a UA-GEC gold row is marked
contested, the workflow suppresses that lookup finding but keeps the module
eligible for Tier 2 in LLM-eligible families. This avoids a recall hole where a
noisy gold row hides a real b1-plus or seminar issue from reviewer judgment.
