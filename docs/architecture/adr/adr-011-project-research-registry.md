# ADR-011: Project Research Registry — bounded cold-start discovery and task-scoped adoption

**Status**: Accepted
**Date**: 2026-07-11
**Deciders**: Krisztian (project owner, accountable); Codex orchestrator (epic owner — scope/integration/disposition); Claude (architecture worker); Gemini 3.1 Pro High (independent cross-family review PASS, bridge #2458, 2026-07-11).
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
2. **Hash-only manifest pointer (global registry hash).** `/api/state/manifest` gains one compact `{hash, url}` research component (≤ 512 bytes, unconditional). This hash is a **single global** hash over the routing-relevant projection of the whole registry (not the digest bodies); any record change flips it for **all** clients.
3. **Filtered, changed pointers — default silence, context-specific ETag.** A proposed `/api/knowledge/manifest` returns IDs, states, hashes, and routing metadata (no digest bodies), and carries its **own role/task-context-specific ETag** over just the projection that client would see. Orientation/bootstrap surface **at most the top relevant *changed* pointers** for the current task; an unrelated task receives none.
4. **Two distinct routers: cold-start pointers vs dispatch relevance.** Cold start knows only the agent's **role** (no task family, track, or owned paths yet), so it uses a narrow, opt-in `cold_start_roles` allow-list to announce **at most five pointers per role** — never a record body. Dispatch/build resolves relevance with the **full AND router** over task family, track, role, and owned paths. Compact record bodies are fetched on demand, capped, and **never** fetched automatically at cold start.
5. **Lifecycle + adoption gate.** Records move `proposed → adopted → deferred → superseded` with gate-enforced invariants (below). "Research is not adoption": a finding is `adopted` only when it resolves to a real consumer (code, prompt, rubric, decision, test, corpus intake, or owned issue).
6. **Strict separation from `sources.db`.** Project-knowledge lookup is a small deterministic index/router over the registry + tracked digests. These documents are **never** added to `sources.db` or its embeddings; a regression test proves no retrieval leakage.

### Lifecycle states and invariants

| State | Meaning | Gate-enforced invariant |
|---|---|---|
| `proposed` | Actionable finding, not yet operational | If actionable, MUST reference exactly one issue owned by exactly one stream epic |
| `adopted` | Wired into a real consumer | MUST carry a **typed, resolvable** consumer `{kind, ref}` (kind ∈ path/prompt/rubric/decision/test/issue/corpus) that resolves deterministically in-tree |
| `deferred` | Deliberately not acted on now | MUST carry a `reason` |
| `superseded` | Replaced by a newer record | MUST carry a valid `replacement` record id that exists |

Cross-cutting invariant — **hash/digest drift invalidates the entry until reconciled**: if a record's `content_hash` no longer matches its digest projection, the validator marks **that record** invalid and the knowledge router excludes **only that record** from routing until reconciled. CI blocks on the affected record and prints an actionable reconciliation command; unrelated records keep routing.

**Stable, deterministic hash projection.** `content_hash` is never computed over an entire living digest file (which churns on any unrelated edit). It covers exactly one of: (a) a **dedicated compact per-record digest** (`docs/references/research-digests/<id>.md`), or (b) an **explicit machine-delimited record section** inside a shared digest (bounded by stable `<!-- record:<id> -->` … `<!-- /record:<id> -->` fences). The projection is normalized before hashing — **canonical normalization**: strip the delimiter fences, normalize line endings to `\n`, strip trailing whitespace per line, collapse a trailing blank-line run to none, UTF-8 encode, then `sha256`. The validator applies the identical normalization so the hash is reproducible across machines.

**Reconciliation workflow.** Updating an expected hash is an **intentional, opt-in** action, never an automatic side effect. `scripts/audit/check_research_registry.py` runs in two modes: `--check` (CI/default) **only reports** drift and never mutates the registry; `--reconcile` recomputes and writes `content_hash` for the drifted records after the human/agent has reviewed the digest change. When `--check` finds drift it names the record and emits the exact command, e.g. `check_research_registry.py --reconcile --id <record-id>`, so reconciliation is a single deliberate step.

### Proposed schema (shape, not frozen)

Per record in `docs/references/research-registry.yaml`:

```yaml
- id: unlp-2026-cefr-assessment        # stable slug, never reused
  title: Automated CEFR-Level Assessment for Ukrainian Texts (Kanishcheva & Kopotev)
  summary: Deterministic linguistic features (tree depth, lexical diversity) beat XLM-R/GPT for UK CEFR.
  content_hash: sha256:…               # over the record's compact digest projection (below), NOT a whole living file
  state: proposed                      # proposed | adopted | deferred | superseded
  provenance:
    digest: docs/references/research-digests/unlp-2026-cefr-assessment.md   # dedicated compact per-record digest
    digest_anchor: null                # OR a machine-delimited section within a shared digest; exactly one of digest/digest_anchor
    source_url: https://aclanthology.org/2026.unlp-1.18/                    # public, may be null
  routing:                             # dispatch/build AND router — every present dimension must match
    roles: [quality, pedagogy]
    task_families: [difficulty-gate, module-text-audit]
    tracks: [core, a1, a2, b1, b2]
    owned_paths: ["scripts/audit/**"]
  cold_start_roles: [quality]          # opt-in, ≤5 total across the registry per role; empty/absent → no cold-start pointer
  ownership:
    issue: 4952
    stream: 4274                       # core-quality epic #4952 was attached to during #4969 creation (was orphaned when discovered)
  consumer: null                       # required when state == adopted; typed ref: {kind, ref} (see below)
  reason: null                         # required when state == deferred
  replacement: null                    # required when state == superseded
  access_class: tracked-digest         # tracked-digest (default) | public-url | private-local
```

**Typed consumer (required when `state == adopted`).** `consumer` is not free text — it is a typed, deterministically resolvable reference:

```yaml
  consumer:
    kind: test                         # path | prompt | rubric | decision | test | issue | corpus
    ref: scripts/audit/tests/test_difficulty_gate.py::test_cefr_features
```

The validator resolves each `kind` deterministically: `path`/`prompt`/`rubric`/`test` → the file (and optional `::anchor`/symbol) exists in-tree; `decision` → a live id in `docs/decisions/decisions.yaml`; `issue` → a numeric id resolvable via the issue tooling; `corpus` → a declared intake entry. Resolution failure marks the record invalid — an `adopted` record with a dangling consumer never validates.

**Routing algebra (dispatch/build → relevance).** The router matches a task's `{role, task_family, track, owned_paths}` against each record's `routing.*` as a **conjunction (AND) across every routing dimension the record specifies**. For each dimension *present* on the record, the task's value MUST intersect it; a dimension *omitted* from the record is a wildcard (matches any task). Critically, a task that lacks a value for a dimension the record requires does **not** match. So a `core`-track record whose `task_families: [difficulty-gate]` is set will **not** surface for a `core`-track `tts` task — track alone is insufficient. `owned_paths` uses glob patterns matched against the dispatch worktree's changed/owned paths. Default is no match → no pointer. This is intentionally a boolean/keyword router, **not** a semantic/vector matcher (see Alternatives).

**Cold-start algebra (role only).** Cold start has no task family/track/owned paths, so it cannot run the AND router. It uses `cold_start_roles` only: a record announces a pointer at cold start solely to roles it explicitly lists, capped at **five pointers total per role** across the whole registry (deterministic tie-break by record id). A record with empty/absent `cold_start_roles` is invisible at cold start — the client still receives the registry hash/URL (change-awareness) but no pointer and no body.

`access_class` values: `tracked-digest` (default — digest is committed, worktree-safe), `public-url` (digest may be re-fetched from a public source into an allowlisted cache), `private-local` (raw source is gitignored/local-only; **never** auto-provisioned into worktrees).

**Digest content policy (copyright guard).** Tracked digests contain summaries, paraphrases, and **bounded quotations with provenance** — never copied papers, figures, or large verbatim passages. P1 validation enforces this where deterministically possible: per-record quoted-span length caps, a required `source_url`/citation on any quoted span, and a digest-size ceiling; violations fail CI. This keeps the tracked corpus fair-use and worktree-safe.

### Cold-start budgets, caching, invalidation, failure behavior

**Hard budgets** (design contracts from #4969 — CI measures serialized bytes on deterministic fixtures every change; these are *contracts*, not current-state measurements). **Serialized UTF-8 byte budgets are the normative gate.** Token counts are a **deterministic estimate only**, pinned to a documented conservative formula so CI never depends on a live tokenizer: `est_tokens = ceil(utf8_bytes / 2)`. Two bytes/token deliberately over-counts for both English and Ukrainian (Cyrillic is 2 UTF-8 bytes/char, so this bounds even worst-case Ukrainian payloads); it is a ceiling for budgeting, not a measured tokenizer output.

| Surface | Budget (normative = bytes) |
|---|---|
| Total `/api/state/manifest` response | **< 2 KB** (unchanged existing target; the research component fits *within* it) |
| Unconditional `/api/state/manifest` research component | **≤ 512 bytes** |
| Filtered changed-pointer payload | **top 5 records and ≤ 1.5 KB** |
| One compact record body | **≤ 4 KB** (est. ≈ 2,048 tokens via `ceil(bytes/2)`) |
| Automatic per-cold-start record-body fetch | **≤ 8 KB total**; further reads require explicit task demand |
| Warm unchanged state | verified **304**, **zero** research-body tokens injected |

**Two-tier ETag/304 + invalidation.** The knowledge endpoint reuses the existing `_matches_etag()` pattern (`rules_router.py:42`) at three independent tiers:

- **Global manifest hash** (`/api/state/manifest`): a single registry-wide hash. Editing *any* record flips it, so every client sees the manifest research component change — this tier only signals "something in the registry moved," not what.
- **Filtered projection ETag** (`/api/knowledge/manifest`): scoped to the requesting role/task context. Because it hashes only the projection that client would see, a client whose relevant set is unchanged can send `If-None-Match: "<projection-etag>"` **after the global hash has already changed** and still receive `304` with an empty body. This is the mechanism that keeps unrelated clients at zero research tokens even during churn.
- **Per-record hash/ETag** (`/api/knowledge/record/{id}`): each record body keeps its own `content_hash`; a warm client re-requesting an unchanged body gets `304`.

Changing one registry record flips the global manifest hash and that record's per-record hash, and flips the filtered-projection ETag **only for contexts that record routes to** — an unrelated warm client still gets `304` on its filtered projection despite the global hash moving.

**Failure / degradation (fail-open, never block boot):**

- Registry file missing/malformed → manifest **omits** the research component; `orient`/`bootstrap` proceed unchanged; a warning is logged. Cold start never hard-fails on the registry.
- Knowledge endpoint slow/erroring → same isolation as orient collectors (`_cached_orient_section` TTL + hard timeout + fallback, `main.py:599`): degrade to zero research pointers.
- Budget exceeded at runtime → truncate to top-N and **log the drop explicitly** (name what was dropped — no silent truncation); CI already fails the byte/token fixture, so this is a belt-and-suspenders runtime guard.
- Invalidated (hash-drift) record → excluded from routing until reconciled; surfaced in the staleness view (P4).

**Runtime kill switch (rollout safety).** A single default-safe configuration flag — `research_registry.enabled` (config, env-overridable) — gates the entire feature. **Default during rollout: `false`** (manifest omits the research component; `/api/knowledge/*` returns an empty/disabled projection; the router surfaces zero pointers), reproducing exact current behavior. Flipping it `true` enables the feature without a code change; flipping it back `false` is an instant, in-place disable — **no revert PR and no redeploy required**. This makes rollback a config toggle, not a deploy, and lets the pilot run behind the flag while unrelated agents are wholly unaffected.

### P6 pilot result and rollout decision

The real three-record UNLP pilot is recorded in
[`research-registry-pilot.md`](../../references/research-registry-pilot.md).
It protects five explicit task contexts, exact canonical UTF-8 payload/body
measurements, state-manifest delta, and endpoint-level warm-cache `304` reads in
`scripts/audit/check_research_registry_pilot.py`. The result is **GO for a
controlled local rollout when a task supplies explicit scoped context or a
session already knows its assigned functional role**. `MonitorClient().bootstrap()`
without a role remains generic and pointer-free; there is no hidden default role.

The compiled feature default remains fail-safe disabled. The gitignored live flag
is a local opt-in, and rollback is setting it false or removing it — no source
revert, task-store rewrite, or telemetry deletion. This decision does not switch
every environment on. New research ingestion remains schema/adoption-gated.

**P5 remains NO-GO / condition not triggered.** The three bounded digests are
sufficient, CEFR adoption shipped without raw transport, and deferred TTS/GEC
work is blocked by ownership/product/licensing. Reopen only for a specific missing
datum plus a blocked routed task, proof that digest/public manual access is
insufficient, repeated need, and rights allowing automated caching.

### P4 — strict adoption gate: cache authority window and partial-metric semantics

**Cache authority window.** `scripts/audit/check_research_registry.py --strict-adoption` and `GET /api/knowledge/monitor` both gate ownership/issue-consumer proof on a membership cache (`batch_state/issue_stream_audit.json`, gitignored, written by `scripts/orchestration/issue_stream_audit.py`), never the network directly. A cache is authoritative only when:

- `generated_at` is a finite, non-boolean numeric timestamp;
- its age is **≤ `max_age_s`** (default **3600s** — matches the auditor's own session-setup refresh cadence);
- its age is **not more than 300s (`CACHE_FUTURE_SKEW_S`) in the future** — clock skew or a corrupted/hand-edited timestamp must not read as "fresh forever" just because the age computes negative;
- every `effective_membership` entry is structurally + semantically valid: positive-int epics, non-empty stream names, a known `via` (`native`/`body`), and a `unique_stream` bool **consistent with the epic count** — exactly one effective epic, not merely one stream name (two epics sharing a stream are still ambiguous);
- `open_issue_numbers`, if present, is a list of positive ints.

Any violation fails the whole cache **closed** (`read_membership_index` → `None`) — never a partial/best-effort read, never a raised exception. The `corpus` resolver (`scripts.audit.atlas_intake_registry.is_registered_source_family`) needs no cache at all: it is a static, offline, always-available table, injected unconditionally into the strict gate, the monitor, **and** ordinary `--check`/`--reconcile` (PR #4998 final review) — unlike the `issue` resolver, which stays uninjected under ordinary `--check` because it genuinely needs a fresh, live cache. `validate_registry(..., corpus_resolver=None)` itself is unchanged and still fails closed for any caller that omits authority.

**Ownership is historical; issue-consumer liveness is not.** `effective_membership` indexes every native/body-linked child a stream epic returns, open or closed — record *ownership* (`ownership.issue` on a `proposed` record) proves the epic uniquely tracked that issue and does not un-prove itself when the issue is later closed (implementation done). Issue *consumer* health (`consumer: {kind: issue, ...}` on an `adopted` record) is a stricter, separate proof: it additionally requires the ref to appear in `open_issue_numbers`, because a consumer names ongoing work, not a completed one. `make_membership_resolver` checks only `effective_membership`; `make_issue_resolver` checks `effective_membership` **and** `open_issue_numbers`. A closed, uniquely-owned issue therefore passes ownership and fails as a consumer — this is by design, not a bug (PR #4998 corrective pass).

**Partial-metric semantics (consumption telemetry).** The monitor's telemetry scan (`scripts/research/observability.py::_scan_telemetry`) is bounded (`MAX_SCAN_BYTES` = 64 MiB total, `MAX_LINE_CHARS` = 1 MiB per line) and scans **newest day first** — so a byte cap drops older, less-actionable days rather than hiding today's activity behind history. Any partial coverage (byte cap, an unreadable file, or an oversized/no-newline line) sets `partial: true` and a `cap_reason` (`byte_cap`/`unreadable_file`/`oversized_line`), plus `files_in_window`/`files_scanned`/`files_skipped` so the gap itself is visible — no silent truncation.

Under `partial: true`, `surfaced_never_consumed` (a **definitive negative** claim — "genuinely never consumed") is reported **`null`**, never a number: a consumption event could exist outside what was actually scanned, so asserting it would be dishonest. This applies at **every** level the field appears — the top-level aggregate, each `per_record[id]` bucket, and the `unknown_research_ids` bucket — not only the top level; a hidden consuming event could be hiding behind an unreadable file or a discarded oversized line for exactly one record, so a per-record `null` is required too (PR #4998 final review). The raw observed count is still available as `surfaced_never_consumed_observed` (mirrored per-record as well) — a **lower bound**, like every other positive/raw count in the payload (`surfaced_events`, `consumed_events`, `surfaced_pairs`, `consumed_pairs`, `distinct_pairs`): missing data can only under-count these, never manufacture a false positive, so they are safe to report even when coverage is incomplete.

Every P3 event row (`research_pointer_surfaced` / `research_record_consumed`) is validated against its field contract — bounded `task_id`/`research_id`, a surface matching the event type, and (for consumption) `status ∈ {200, 304}` — **before** it can affect any aggregate; a row of the right type that fails this contract counts as `malformed_lines`, never silently as noise from "some other event type."

The `MAX_SCAN_BYTES` cap bounds **total bytes returned by the telemetry file reader**, not just bytes that make it into a parsed event: every binary read request is limited by the shared budget before it occurs, and bytes discarded while draining an oversized (no-newline) line are included in that same exact total. A pathological multi-GB no-newline file therefore cannot be read past the cap while `bytes_scanned` stays near zero — the scan stops mid-drain, safely, the moment the budget is exhausted. Separately, the oversized check compares physical line *content* length against `MAX_LINE_CHARS`, not a raw read length: a line whose content is exactly `MAX_LINE_CHARS` chars plus its own trailing newline is never treated as needing a drain (PR #4998 final review).

### Privacy / worktree policy

- **Tracked digests are the default and only auto-provisioned surface.** They are committed, so they already reach every worktree with no new symlink.
- **No blanket private symlink.** `_provision_data_symlinks()` is **not** extended to add `docs/references/private/`. Raw papers stay gitignored and absent from worktrees.
- **Raw re-reading, if ever needed, is opt-in and per-record** (P5, gated on the pilot proving need): either an allowlisted per-record path or a public-download cache keyed on `access_class: public-url`. `private-local` records never leave the local machine.

## Alternatives considered

- **Global prompt injection of research into every agent** → rejected: violates "pointers before payloads" and "relevance before broadcast"; blows cold-start budgets; injects irrelevant context into unrelated (UI/CI) tasks. This is the exact bloat the epic exists to prevent.
- **Ingest `docs/references/` into `sources.db`** → rejected: `sources.db` is the learner-content/source corpus and is *recreated* on rebuild (`build_sources_db.py`; ADR-006). Mixing internal project research into it pollutes curriculum retrieval and couples two unrelated lifecycles. A regression test will prove no leakage.
- **GitHub issues only (no registry)** → rejected: issues track *work*, not *findings*, and have no hash/budget/lifecycle contract, no digest provenance, and no deterministic routing. #4952 is the concrete failure of issues-as-registry: it was **orphaned when discovered** (no parent), and was only **attached to core-quality epic #4274 during #4969 creation** — parented under a quality epic, still not routed as a research consumer.
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

- **P1 — Registry + validation.** Add `docs/references/research-registry.yaml`; schema under `schemas/research_registry.schema.json`; loader/validator `scripts/audit/check_research_registry.py` with `--check` (report-only, CI/default — **never mutates**) and `--reconcile [--id …]` (intentionally rewrites drifted `content_hash`). Validate lifecycle invariants, provenance, canonical-normalized per-record `content_hash`, typed-consumer resolution, stream-ownership, and the **digest copyright guard** (bounded quoted-span length, required provenance on quotes, digest-size ceiling). Seed the UNLP records + compact per-record digests. *Tests*: schema-valid fixtures, each invariant's negative case, hash-drift detection, `--check` non-mutation, copyright-guard rejection of an over-long verbatim span. *Migration*: none (new file + derived optional index rebuilt from YAML; never in `sources.db`). *Rollback*: revert PR.
- **P2 — Bounded discovery API.** Add the global-hash `{hash, url}` research component to `state_router.py` `manifest()` (total manifest still < 2 KB); add `/api/knowledge/manifest` (IDs/states/hashes/routing, no bodies, context-specific ETag) + `/api/knowledge/record/{id}` (compact body, capped, per-record ETag); wire all three tiers via `_matches_etag`. Gate the whole surface behind `research_registry.enabled` (default `false`). *Tests*: byte budget fixtures for every budget incl. total-manifest < 2 KB; two-tier `304` (global hash flips, filtered projection still `304`) end-to-end; per-record hash invalidation; kill-switch off = current behavior. *Rollback*: config toggle or revert; manifest key absence is tolerated by clients.
- **P3 — Task-scoped routing.** Deterministic **AND** router matching `{role, task_family, track, owned_paths}` (present dimensions conjunctive, omitted = wildcard); separate role-only `cold_start_roles` announcer (≤5/role) for orient/bootstrap; dispatch context surfaces top changed pointers; record which research IDs each task consumed. *Tests*: routing TP/TN across all four dimensions incl. same-track/wrong-family negative; cold-start announces only `cold_start_roles` and never a body.
- **P4 — Adoption gate + observability.** Enforce `adopted`→typed-resolvable-consumer and actionable-`proposed`→one-stream-owned-issue; expose stale/orphaned/deferred/superseded plus adoption rate, consumption counts, and dead-consumer counts via a monitor endpoint. *Tests*: gate rejects unresolvable typed consumer, orphaned proposed, missing reason/replacement; observability surfaces a dead consumer.
- **P5 — Raw-source access (only if the pilot proves need).** Opt-in per-record allowlist or public-download cache keyed on `access_class`; still no blanket `docs/references/private/` symlink. *Tests*: `private-local` never provisioned; `public-url` cache is allowlisted.
- **P6 — UNLP pilot + rollout decision.** Run discovery FP/FN fixtures; measure payload size + warm-cache behavior + recall/precision; publish the measured report; approve wider ingestion or revise.

**Observability**: CI byte/token measurement job on fixtures; per-task consumed-research-ID log; monitor endpoint listing stale/orphaned/deferred/superseded findings. Beyond raw lifecycle-state counts, the endpoint exposes **adoption/consumption metrics**: adoption rate (`adopted` ÷ actionable records), per-record consumption counts (how many dispatches actually consumed each pointer, from the consumed-ID log), and **dead-consumer counts** — `adopted` records whose typed consumer no longer resolves, and pointers surfaced but never consumed over a window. These turn silent registry rot into a visible, actionable signal rather than a count of states.

## Pilot fixtures (UNLP 2025/2026 — positive and negative discovery)

Seed from the two existing UNLP docs and exercise every routing class:

| Task (role · family · track · paths) | Expected discovery |
|---|---|
| Core-quality difficulty task (`quality`·`difficulty-gate`·`core`·`scripts/audit/**`) | **Positive**: `unlp-2026-cefr-assessment` + issue #4952 surface |
| TTS task (`tts`·`tts`·`—`·`scripts/tts/**`) | **Positive**: `unlp-2025-stress-tts` surfaces (issue #4696) |
| Reviewer-prompt task (`reviewer`·`reviewer-prompt`·`—`·`agents_extensions/**`) | **Positive**: `unlp-2026-gec-minimal-edit` surfaces |
| Same-track, wrong-family task (`pedagogy`·`module-build`·`core`·`curriculum/**`) | **Negative (AND proof)**: `unlp-2026-cefr-assessment` does **not** surface — track intersects (`core`) but `task_families` does not (`module-build` ∉ `difficulty-gate`), so the conjunction fails |
| Unrelated UI/CI task (`frontend`/`infra`·`ui`/`ci`·`—`·`site/**`) | **Negative**: no UNLP body, no irrelevant pointer |
| Edit one UNLP record | Flips the **global** `/api/state/manifest` hash for all clients, but a warm client outside the edited record's routed contexts still gets `304` on its **filtered projection** ETag; only routed contexts see the change |

The pilot must produce a measured report: payload size, warm-cache behavior, relevant-record recall, irrelevant-record precision, adoption status — at least three correctly routed findings, one irrelevant-task exclusion, and one real operational adoption (#4952).

## Review gate and acceptance criteria

**Review gate**: independent **cross-family** review (a model family other than the author's, per repo policy) before any implementation PR merges. Discussion or a same-family swarm does not satisfy the gate. This P0 ADR PR itself must not be self-approved, auto-merged, or merged by the author.

**Measurable acceptance criteria** (mirrors #4969; all enforced by deterministic tests in P1–P6):

- No complete research document enters cold start; the total `/api/state/manifest` response stays < 2 KB and every component byte budget passes CI (bytes normative; tokens via the pinned `ceil(bytes/2)` estimate).
- Two-tier `304` passes end-to-end: after a record edit flips the global manifest hash, an unrelated client still receives `304` on its filtered-projection ETag; per-record body hash invalidation is exercised.
- Routing tests cover TP + TN across role, task family, track, and owned path — including the **same-track/wrong-family negative** proving the AND conjunction (not OR) fails closed.
- A regression test proves project research never leaks into `sources.db` retrieval.
- `adopted` records resolve to a **typed** `{kind, ref}` consumer; actionable `proposed` records have exactly one stream-owned issue.
- Digest copyright policy holds: no large verbatim passages; quoted spans are bounded and carry provenance (enforced where deterministic).
- Hash projection is stable (per-record digest/section, canonically normalized); `--check` never mutates and drift blocks only the affected record with a `--reconcile` command.
- The runtime kill switch defaults safe (`research_registry.enabled=false`) and toggles the feature on/off with no revert or redeploy.
- Raw private sources are inaccessible by default and never blanket-provisioned.
- The UNLP pilot shows ≥ 3 correctly routed findings, 1 irrelevant-task exclusion, 1 real adoption.
- Final docs state measured cold-start byte cost (and estimated tokens) and discovery precision/recall; observability reports adoption rate and dead-consumer counts.

## Verification

- Validator: `scripts/audit/check_research_registry.py` (P1) — lifecycle/provenance/hash/ownership.
- Budget CI: deterministic byte/token fixtures (P2).
- Routing CI: TP/TN discovery fixtures (P3); leakage regression test vs `sources.db`.
- Pilot report: measured payload/recall/precision (P6).
- ADR staleness: `scripts/audit/check_adrs.py` (Proposed → 14-day clock until this ADR reaches Accepted after review).
