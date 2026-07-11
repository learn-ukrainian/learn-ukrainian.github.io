# ADR-011: Project Research Registry — bounded cold-start discovery and task-scoped adoption

**Status**: Proposed
**Date**: 2026-07-11
**Deciders**: Krisztian (project owner, accountable); Codex orchestrator (epic owner — scope/integration/disposition); Claude (architecture worker, this draft). Pending cross-family review gate (independent, non-authoring family) before Accepted.
**Related**: epic [#4969](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4969) (parent stream [#4707](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4707) — Infra & harness reliability); pilot consumer [#4952](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4952) (deterministic text-difficulty gate); [#4696](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4696) (TTS); [#4913](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4913) (harness); `docs/references/unlp-2025-2026-findings.md`; `docs/references/unlp-reading-notes.md`; ADR-005 (wiki knowledge base), ADR-006 (compile-layer retrieval — `sources.db` boundary).

> **Scope note**: This ADR is longer than the project's one-page norm because epic #4969's P0 explicitly asks for "an ADR *or equivalent plan* covering schema, routing, budgets, cache invalidation, privacy, and failure behavior." It therefore doubles as the epic's P0 implementation plan (sections *Implementation plan* and *Pilot fixtures*). Implementation slices (P1–P6) each remain one-concern PRs behind their own review gate; this document freezes the *decision*, not the code.

## Context

The UNLP 2025/2026 research was documented thoroughly (`docs/references/unlp-2025-2026-findings.md`, `docs/references/unlp-reading-notes.md`) but is not automatically visible to later agents. There is a gap between **research saved** and **research operationally adopted**, and that gap is invisible in the tooling. Two concrete symptoms:

- A method-level finding (e.g. UNLP 2026.unlp-1.13's Ukrainian minimal-edit GEC prompt rules) sits in a reference doc that no writer/reviewer cold-start path reads.
- A build-a-thing finding (UNLP 2026.unlp-1.18 → the difficulty gate, #4952) can be filed as an issue and still be orphaned from any operational owner.

**Verified current-state flow** (every claim below has a path/line or issue URL; raw evidence is in the PR body):

1. **Cold-start manifest has no research component.** `scripts/api/state_router.py:1799` `manifest()` returns exactly `rules`, `session`, `orient`, `inbox`, `activity` (target < 2 KB). There is no `knowledge`/`research` key.
2. **Bootstrap fetches only rules + session.** `scripts/ai_agent_bridge/monitor_client.py:191` `bootstrap()` returns `{"rules", "session"}`, each cached by the manifest's per-component content hash (`rules_hash()` at `scripts/api/rules_router.py:193`, `session_hash()` at `scripts/api/session_router.py:281`).
3. **`/api/orient` has no knowledge section.** `scripts/api/main.py` `_orient_section_specs()` (≈ line 695) enumerates `git, issues, pipeline, runtime, delegate, bridge_pending, wiki, governance, health, session_hints` — no research/knowledge collector. `_collect_session_hints_orient_data()` (`main.py:567`) globs `SESSION_STATE_DIR/*.md` (session-state handoffs), **not** durable research references.
4. **Module research discovery does not search `docs/references/`.** `scripts/build/linear_pipeline.py:1146` `build_knowledge_packet()` assembles from compiled wiki (`_build_wiki_packet`), dictionary context, and textbook excerpts only. `rg 'docs/references'` over `scripts/build`, `scripts/api`, `scripts/ai_agent_bridge` returns **zero** hits.
5. **Worktrees do not receive raw private papers.** `scripts/delegate.py:1163` `_provision_data_symlinks()` symlinks exactly `data/vesum.db`, `data/sources.db`, `.venv`, `node_modules`, `site/node_modules` — nothing under `docs/references/`. `docs/references/private/` is gitignored (`.gitignore:132`) and absent from delegated worktrees.
6. **`sources.db` is the learner-content corpus and is recreated on rebuild.** It holds FTS5 indices over textbooks/literary/dictionaries/VESUM/Wikipedia and is rebuilt by `scripts/wiki/build_sources_db.py` (ADR-006 records embeddings live *outside* it precisely because rebuild recreates it). It does not ingest `docs/references/`.
7. **ETag/304 already exists on cold-start components.** `scripts/api/rules_router.py:137` honors `If-None-Match: "<hash>"` → `304 Not Modified` with empty body via the shared `_matches_etag()` helper (`rules_router.py:42`); `scripts/api/session_router.py:239` reuses it. The manifest publishes the hash; the component endpoint enforces the conditional request. **The registry reuses this existing pattern — it does not invent a new caching layer.**

## Decision

Add a **source-controlled Project Research Registry**: a tracked YAML file of one-record-per-actionable-finding plus tracked human-readable digests, surfaced to agents through a **pointer-only, hash-addressed, task-scoped** discovery path that reuses the existing manifest/ETag architecture. Six load-bearing commitments:

1. **Tracked registry + tracked digests, never raw payloads in cold start.** Registry at `docs/references/research-registry.yaml`; each record points to a committed digest (the existing UNLP findings/notes docs, or a per-record digest file). Cold start receives a hash and, at most, a few compact *pointers* — never a full research document.
2. **Hash-only manifest pointer.** `/api/state/manifest` gains one compact `{hash, url}` research component (≤ 512 bytes, unconditional). The hash covers the routing-relevant projection of the registry, not the digest bodies.
3. **Filtered, changed pointers — default silence.** A proposed `/api/knowledge/manifest` returns IDs, states, hashes, and routing metadata (no digest bodies). Orientation/bootstrap surface **at most the top relevant *changed* pointers** for the current task; an unrelated task receives none.
4. **Task-scoped lookup at dispatch/build time.** Relevance is resolved from **task family, track, role, and owned paths** — not from generic agent identity. Compact record bodies are fetched on demand, capped.
5. **Lifecycle + adoption gate.** Records move `proposed → adopted → deferred → superseded` with gate-enforced invariants (below). "Research is not adoption": a finding is `adopted` only when it resolves to a real consumer (code, prompt, rubric, decision, test, corpus intake, or owned issue).
6. **Strict separation from `sources.db`.** Project-knowledge lookup is a small deterministic index/router over the registry + tracked digests. These documents are **never** added to `sources.db` or its embeddings; a regression test proves no retrieval leakage.

### Lifecycle states and invariants

| State | Meaning | Gate-enforced invariant |
|---|---|---|
| `proposed` | Actionable finding, not yet operational | If actionable, MUST reference exactly one issue owned by exactly one stream epic |
| `adopted` | Wired into a real consumer | MUST carry a **resolvable** operational consumer (path/prompt/rubric/decision/test/issue that exists) |
| `deferred` | Deliberately not acted on now | MUST carry a `reason` |
| `superseded` | Replaced by a newer record | MUST carry a valid `replacement` record id that exists |

Cross-cutting invariant — **hash/digest drift invalidates the entry until reconciled**: if a record's `content_hash` no longer matches its digest, the validator marks the record invalid and the knowledge router excludes it from routing until a human/agent reconciles the hash. CI blocks on drift.

### Proposed schema (shape, not frozen)

Per record in `docs/references/research-registry.yaml`:

```yaml
- id: unlp-2026-cefr-assessment        # stable slug, never reused
  title: Automated CEFR-Level Assessment for Ukrainian Texts (Kanishcheva & Kopotev)
  summary: Deterministic linguistic features (tree depth, lexical diversity) beat XLM-R/GPT for UK CEFR.
  content_hash: sha256:…               # over the pointed-to digest projection
  state: proposed                      # proposed | adopted | deferred | superseded
  provenance:
    digest: docs/references/unlp-reading-notes.md#2026.unlp-1.18   # TRACKED pointer
    source_url: https://aclanthology.org/2026.unlp-1.18/           # public, may be null
  routing:
    roles: [quality, pedagogy]
    task_families: [difficulty-gate, module-text-audit]
    tracks: [core, a1, a2, b1, b2]
    owned_paths: ["scripts/audit/**"]
  ownership:
    issue: 4952
    stream: 4274                       # owning stream epic (see correction note in PR)
  consumer: null                       # required when state == adopted
  reason: null                         # required when state == deferred
  replacement: null                    # required when state == superseded
  access_class: tracked-digest         # tracked-digest (default) | public-url | private-local
```

**Routing inputs (dispatch/build → relevance).** The router matches a task's `{role, task_family, track, owned_paths}` against each record's `routing.*`. `owned_paths` uses glob patterns matched against the dispatch worktree's changed/owned paths. A record matches if any dimension intersects; default is no match → no pointer. This is intentionally a boolean/keyword router, **not** a semantic/vector matcher (see Alternatives).

`access_class` values: `tracked-digest` (default — digest is committed, worktree-safe), `public-url` (digest may be re-fetched from a public source into an allowlisted cache), `private-local` (raw source is gitignored/local-only; **never** auto-provisioned into worktrees).

### Cold-start budgets, caching, invalidation, failure behavior

**Hard budgets** (design contracts from #4969 — CI measures serialized bytes + estimated tokens on deterministic fixtures every change; these are *contracts*, not current-state measurements):

| Surface | Budget |
|---|---|
| Unconditional `/api/state/manifest` addition | **≤ 512 bytes** |
| Filtered changed-pointer payload | **top 5 records and ≤ 1.5 KB** |
| One compact record body | **≤ 4 KB / ≈ 1,200 tokens** |
| Automatic per-cold-start record-body fetch | **≤ 8 KB total**; further reads require explicit task demand |
| Warm unchanged state | verified **304**, **zero** research-body tokens injected |

**ETag/304 + invalidation.** The knowledge endpoint reuses the existing `_matches_etag()` pattern (`rules_router.py:42`): the manifest publishes the research hash; a client sending `If-None-Match: "<hash>"` gets `304` with an empty body. Changing one registry record changes only that record's `content_hash` and the registry projection hash, invalidating **only** the relevant knowledge cache path — an unrelated warm client still gets `304`.

**Failure / degradation (fail-open, never block boot):**

- Registry file missing/malformed → manifest **omits** the research component; `orient`/`bootstrap` proceed unchanged; a warning is logged. Cold start never hard-fails on the registry.
- Knowledge endpoint slow/erroring → same isolation as orient collectors (`_cached_orient_section` TTL + hard timeout + fallback, `main.py:599`): degrade to zero research pointers.
- Budget exceeded at runtime → truncate to top-N and **log the drop explicitly** (name what was dropped — no silent truncation); CI already fails the byte/token fixture, so this is a belt-and-suspenders runtime guard.
- Invalidated (hash-drift) record → excluded from routing until reconciled; surfaced in the staleness view (P4).

### Privacy / worktree policy

- **Tracked digests are the default and only auto-provisioned surface.** They are committed, so they already reach every worktree with no new symlink.
- **No blanket private symlink.** `_provision_data_symlinks()` is **not** extended to add `docs/references/private/`. Raw papers stay gitignored and absent from worktrees.
- **Raw re-reading, if ever needed, is opt-in and per-record** (P5, gated on the pilot proving need): either an allowlisted per-record path or a public-download cache keyed on `access_class: public-url`. `private-local` records never leave the local machine.

## Alternatives considered

- **Global prompt injection of research into every agent** → rejected: violates "pointers before payloads" and "relevance before broadcast"; blows cold-start budgets; injects irrelevant context into unrelated (UI/CI) tasks. This is the exact bloat the epic exists to prevent.
- **Ingest `docs/references/` into `sources.db`** → rejected: `sources.db` is the learner-content/source corpus and is *recreated* on rebuild (`build_sources_db.py`; ADR-006). Mixing internal project research into it pollutes curriculum retrieval and couples two unrelated lifecycles. A regression test will prove no leakage.
- **GitHub issues only (no registry)** → rejected: issues track *work*, not *findings*, and have no hash/budget/lifecycle contract, no digest provenance, and no deterministic routing. #4952's orphan state (unlabeled; parented under a quality epic, not routed as a research consumer) is the concrete failure of issues-as-registry.
- **Full research text in cold start** → rejected: unbounded token cost; defeats the manifest's "collapse steady state to one tiny call" purpose (`state_router.py:1824`).
- **Knowledge graph / vector store / semantic memory platform** → rejected (also a #4969 non-goal): premature abstraction for a corpus of tens of findings; non-deterministic routing conflicts with the project's deterministic-over-hallucination doctrine; ADR-005/006 already chose deterministic retrieval over vector stores for adjacent problems. A boolean keyword/path router is sufficient and auditable.
- **Reuse `session_hints` for research** → rejected: `session_hints` scans transient session-state files (`main.py:567`), which are ephemeral handoffs, not durable, hash-addressed, provenance-bearing findings.

## Consequences

**Positive**:
- Closes the research-saved → research-adopted gap with a bounded, testable contract.
- Cold start stays tiny: pointer-only, hash-gated, default-silent; unrelated tasks pay ~zero.
- Reuses proven manifest/ETag/304 machinery — minimal new surface, no new caching model.
- Adoption is provable: `adopted` requires a resolvable consumer; orphans/stale/deferred/superseded become visible.
- Hard separation keeps curriculum retrieval (`sources.db`) clean.

**Negative / risks**:
- New file + validator + endpoint + tests to maintain (registry rot) → mitigated by hashes, lifecycle invariants, consumer resolution, stream-ownership checks, CI budgets.
- Routing is keyword/path-based, so a mis-tagged record can be missed → mitigated by negative+positive discovery fixtures (below) and the completeness of the pilot report.
- Manual digest/hash reconciliation on source changes → mitigated by drift invalidation + CI block (never silently serves stale research).

**Neutral / follow-ups**:
- The registry is additive and revertible per phase; removing the file or the manifest key restores exact current behavior (fail-open).
- `#4952` ownership should be re-routed as a pilot consumer (see PR note; issue bodies are not edited in this P0).

## Implementation plan (P1–P6 — proposed surfaces, one-concern PRs)

Each slice is its own PR behind the cross-family review gate. Surfaces are *proposed*, not frozen.

- **P1 — Registry + validation.** Add `docs/references/research-registry.yaml`; schema under `schemas/research_registry.schema.json`; loader/validator `scripts/audit/check_research_registry.py` (lifecycle invariants, provenance/`content_hash` checks, stream-ownership check). Seed the UNLP records. *Tests*: schema-valid fixtures, each invariant's negative case, hash-drift detection. *Migration*: none (new file + derived optional index rebuilt from YAML; never in `sources.db`). *Rollback*: revert PR.
- **P2 — Bounded discovery API.** Add the `{hash, url}` research component to `state_router.py` `manifest()`; add `/api/knowledge/manifest` (IDs/states/hashes/routing, no bodies) + `/api/knowledge/record/{id}` (compact body, capped); wire ETag/304 via `_matches_etag`. *Tests*: byte/token budget fixtures for all five budgets; warm-cache `304` end-to-end; per-record hash invalidation. *Rollback*: revert; manifest key absence is tolerated by clients.
- **P3 — Task-scoped routing.** Deterministic router matching `{role, task_family, track, owned_paths}`; surface top changed pointers via `orient`/bootstrap and dispatch context; record which research IDs each task consumed. *Tests*: routing TP/TN across all four dimensions.
- **P4 — Adoption gate.** Enforce `adopted`→resolvable-consumer and actionable-`proposed`→one-stream-owned-issue; expose stale/orphaned/deferred/superseded via a monitor endpoint. *Tests*: gate rejects unresolvable consumer, orphaned proposed, missing reason/replacement.
- **P5 — Raw-source access (only if the pilot proves need).** Opt-in per-record allowlist or public-download cache keyed on `access_class`; still no blanket `docs/references/private/` symlink. *Tests*: `private-local` never provisioned; `public-url` cache is allowlisted.
- **P6 — UNLP pilot + rollout decision.** Run discovery FP/FN fixtures; measure payload size + warm-cache behavior + recall/precision; publish the measured report; approve wider ingestion or revise.

**Observability**: CI byte/token measurement job on fixtures; per-task consumed-research-ID log; monitor endpoint listing stale/orphaned/deferred/superseded findings.

## Pilot fixtures (UNLP 2025/2026 — positive and negative discovery)

Seed from the two existing UNLP docs and exercise every routing class:

| Task (role · family · track · paths) | Expected discovery |
|---|---|
| Core-quality difficulty task (`quality`·`difficulty-gate`·`core`·`scripts/audit/**`) | **Positive**: `unlp-2026-cefr-assessment` + issue #4952 surface |
| TTS task (`tts`·`tts`·`—`·`scripts/tts/**`) | **Positive**: `unlp-2025-stress-tts` surfaces (issue #4696) |
| Reviewer-prompt task (`reviewer`·`reviewer-prompt`·`—`·`agents_extensions/**`) | **Positive**: `unlp-2026-gec-minimal-edit` surfaces |
| Unrelated UI/CI task (`frontend`/`infra`·`ui`/`ci`·`—`·`site/**`) | **Negative**: no UNLP body, no irrelevant pointer |
| Edit one UNLP record | Invalidates **only** that record's knowledge hash/cache path; unrelated warm clients still `304` |

The pilot must produce a measured report: payload size, warm-cache behavior, relevant-record recall, irrelevant-record precision, adoption status — at least three correctly routed findings, one irrelevant-task exclusion, and one real operational adoption (#4952).

## Review gate and acceptance criteria

**Review gate**: independent **cross-family** review (a model family other than the author's, per repo policy) before any implementation PR merges. Discussion or a same-family swarm does not satisfy the gate. This P0 ADR PR itself must not be self-approved, auto-merged, or merged by the author.

**Measurable acceptance criteria** (mirrors #4969; all enforced by deterministic tests in P1–P6):

- No complete research document enters cold start; all five context budgets pass CI.
- Warm-cache `304` and per-record hash invalidation pass end-to-end.
- Routing tests cover TP + TN across role, task family, track, and owned path.
- A regression test proves project research never leaks into `sources.db` retrieval.
- `adopted` records resolve to real consumers; actionable `proposed` records have exactly one stream-owned issue.
- Raw private sources are inaccessible by default and never blanket-provisioned.
- The UNLP pilot shows ≥ 3 correctly routed findings, 1 irrelevant-task exclusion, 1 real adoption.
- Final docs state measured cold-start byte/token cost and discovery precision/recall.

## Verification

- Validator: `scripts/audit/check_research_registry.py` (P1) — lifecycle/provenance/hash/ownership.
- Budget CI: deterministic byte/token fixtures (P2).
- Routing CI: TP/TN discovery fixtures (P3); leakage regression test vs `sources.db`.
- Pilot report: measured payload/recall/precision (P6).
- ADR staleness: `scripts/audit/check_adrs.py` (Proposed → 14-day clock until this ADR reaches Accepted after review).
