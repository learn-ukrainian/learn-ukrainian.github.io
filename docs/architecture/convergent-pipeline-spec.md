# Convergent Pipeline — Implementation Spec (final, patched)

> v4.1. Consolidates v2 + v3 + final-spec-review adversarial passes (Codex + Gemini). All 12 original patches + 7 final-round patches integrated. **Ship scope: everything together, one implementation, one end-to-end review round, test on the stuck A1/M1 module before merge.**

## Goal

v6 build pipeline must converge to `pass` or one of two honest human-dependent terminals. `needs-human-review.yaml` is deleted. No fake-autonomous dead-ends.

## Non-goals

- Removing cross-agent review (ADR-001:35 invariant preserved)
- Removing deterministic `<fixes>` machinery (kept for patch tier)
- Making plan mutable from pipeline (plan stays user-approved source of truth)
- Training the reviewer (reviewer prompt stays static and global; module-memory feeds writer only)

## State machine

```
write (attempt 0) → review
  ↓
  pass?        → publish                           [autonomous terminal]
  fail?        → ladder decides next attempt (1..5 max)

  tier 1: patch            deterministic <fixes>; only if reviewer emitted them
                           and findings are local to prose
  tier 2: section_rewrite  section-local findings only; skip to tier 3 if any
                           finding touches global budgets, dialogue arc,
                           vocabulary pacing, or activity order
  tier 3: full_rewrite     full module regeneration; learned constraints
                           injected into writer prompt
  tier 4: writer_swap      cross-family writer swap; reviewer matrix below
  tier 5: plan_revision    emits plan-revision-request.yaml  [human terminal]

HARD CAP: 5 escalation attempts after initial write.
Cap hit without pass → budget_exhausted.yaml              [human terminal]
```

Ladder does NOT march sequentially. Tier selection is per-attempt, based on finding topology. See "Tier selection logic" below.

## Stall signals (primary; score delta is secondary only)

Escalate when ANY fires:

1. **Hard-floor dimension persists** — any dimension scored < 9 with error evidence (`dim_floor_fail` set; `v6_build.py:1531`) remains sub-9 after the last attempt.
2. **Top-3 normalized findings overlap** — ≥ 2 of top-3 normalized findings from round N-1 remain in round N (overlap by normalized ID, not prose string).
3. **Content hash repeat** — rewrite output hash == previous attempt hash.
4. **Zero-mutation patch** — applied `<fixes>` produced 0 content changes.

Score delta is recorded but never the sole trigger.

## Finding normalization (required for stall signals to work)

Every reviewer finding gets normalized to a stable ID:

```
{dimension, error_class, scope}
  dimension:   one of {linguistic_accuracy, pedagogical_quality, ...}
  error_class: canonical enum (e.g. calque, register_drift, notation_error,
               missing_vocab, paronym_mismatch, stress_error, ...)
  scope:       {section_title, speaker?, target_lexeme?}
```

Normalizer implementation: lookup table (error_class by reviewer keyword pattern) + deterministic scope extraction from finding YAML. Unrecognized → `error_class: unclassified` with the original prose preserved; logged for human review of the normalization rules (the rules improve over time, not the reviewer).

Current findings are prose blobs (`review-structured-r3.yaml:52`). Normalization is a hard prerequisite — without it, signals 2 and 4 don't function.

## Tier selection logic

**Requires a topology classifier.** Current structured findings carry `dimension/severity/location/issue/fix` — nothing that reliably signals `local_to_prose` / `section_local` / `cross_section` / `plan_level`. Without topology classification, tier 1 vs 2 vs 3 collapses to heuristic guessing.

**Topology classifier — required new module:** `scripts/build/finding_topology.py`
- Input: normalized finding with `location` field
- Output: `topology: local_to_prose | section_local | cross_section | plan_level`
- Deterministic rules:
  - `local_to_prose`: `location` points at a single paragraph or sentence, `fix` includes `<fixes>` patch
  - `section_local`: `location` references single H2 section, no other-section references in `issue` text
  - `cross_section`: `location` or `issue` references multiple H2 sections, dialogue arc, vocabulary pacing, activity order, or budget distribution
  - `plan_level`: error_class ∈ {`vocab_density`, `pedagogical_sequence`, `scenario_grammar_misalignment`, `plan_contradiction`} (the Gemini/Codex-defined plan-revision categories)

```
if patch tier available AND reviewer emitted <fixes> AND all findings.topology == local_to_prose:
  → tier 1 (patch)
elif all findings.topology ∈ {local_to_prose, section_local}:
  → tier 2 (section_rewrite)
elif any finding.topology == plan_level AND tier 3 already attempted:
  → tier 5 (plan_revision_request)  [fast-path: skip wasted full_rewrite]
elif top-3 findings have not yet been targeted by full_rewrite:
  → tier 3 (full_rewrite)
elif top-finding-dimension persists AND writer not yet swapped AND allowed reviewer available:
  → tier 4 (writer_swap)
else:
  → tier 5 (plan_revision_request)
```

## Hard-floor priority (critical)

Before selecting tier, reorder findings:
- Any finding tied to a `dim_floor_fail` dimension is auto-elevated to `critical` severity, **ahead of otherwise-higher-severity findings on non-floor dimensions**.
- This prevents chasing a pedagogy 8.5 while linguistic accuracy sits at 7.0 and then hitting `budget_exhausted` with the floor still failing.

## Reviewer assignment matrix (hard invariant, feature-flagged)

| Writer | Reviewer allowed |
|---|---|
| gemini | claude, codex |
| claude | gemini, codex |
| codex  | claude, gemini |

**This is NEW code in Phase B, not reuse.** Only default routing exists in `_determine_reviewer()` (`v6_build.py:4855`). `SELF_REVIEW_DETECTED` audit check is not currently a hard gate (consistent with ongoing Gemini-only capacity workaround).

**Feature flag: `CONVERGENCE_MATRIX_ENFORCED` (default OFF at ship time).**

- OFF (default during Gemini-only capacity): falls back to `_determine_reviewer()` current routing; self-review allowed, identical behavior to today.
- ON (flip when Claude/Codex review capacity returns): matrix enforced. `writer_swap` at tier 4 picks fresh cross-family reviewer. If no allowed reviewer available → **skip tier 4, escalate to tier 5 (plan_revision_request)**. Never self-review as dormant fallback.

Re-run `review-style` after writer_swap (advisory, per `v6_build.py:8555`). `stuck-modules.yaml` surfaces any module hitting tier 5 because of capacity unavailability — single-pane visibility for the operator to know when to flip the flag.

## module-memory.yaml schema

Path: `curriculum/l2-uk-en/{level}/orchestration/{slug}/module-memory.yaml`

```yaml
plan_hash: <sha256 of plans/{slug}.yaml>
plan_version: <int>                         # from plan file
sources_hash: <sha256 of source manifest>   # for replay determinism
                                            # manifest = content hashes (NOT mtimes) of:
                                            #   - VESUM lemma+form tables
                                            #   - FTS5 textbook/literary/dictionary indexes
                                            #   - Правопис file contents
                                            #   - Wiki packet for this slug (curriculum/l2-uk-en/wiki/{level}/{slug}/)
                                            #   - Base writer template file

constraints:                                 # fed to WRITER only (not reviewer)
  - id: c_a1_m1_001                          # normalized, not prose
    dimension: linguistic_accuracy
    error_class: register_drift
    scope:                                   # scope-aware conflict detection
      speaker: teacher
      section: "Привітання в класі"
      target_lexeme: null
    directive: "Teacher uses formal register (ви) in direct address"
    severity: major
    recur_count: 2
    status: active | quarantined | promoted
    learned_at:
      round: 3
      strategy: full_rewrite
      date: 2026-04-18
    source_finding_ids: [f_a1_m1_reg_drift_r2, f_a1_m1_reg_drift_r3]
    conflicts_with_plan: false               # true → auto-quarantine + event
    override_track_level: false              # true if this overrides a promoted constraint

history:                                     # append-only replay log
  - attempt: 1
    strategy: write
    writer: gemini
    writer_model_version: gemini-3.1-pro-preview
    reviewer: claude
    reviewer_model_version: claude-opus-4-6
    score_overall: 8.33
    scores_per_dimension:
      linguistic_accuracy: 7.0
      pedagogical_quality: 8.5
      ...
    dim_floor_fail: [linguistic_accuracy]
    verdict: revise
    content_hash: <sha>
    prompt_hash: <sha>
    contract_snapshot_hash: <sha>
    findings_normalized: [c_a1_m1_001, c_a1_m1_002]
    mutation_summary: null
    decision_reason: initial
    artifacts:
      prompt_path: orchestration/.../write-prompt-r1.md
      review_path: a1/review/sounds-letters-and-hello-review-r1.md
    timestamps:
      started: 2026-04-18T00:00:00Z
      finished: 2026-04-18T00:02:14Z
    cost:
      input_tokens: 45200
      output_tokens: 8300
      wall_clock_s: 134
```

### Quarantine heuristic (scope-aware)

A new or existing constraint is auto-quarantined when:
1. **Same-scope opposite directive** — another active constraint has equal `{speaker, section, target_lexeme}` tuple but contradictory directive. Deterministic, cheap.
2. **Immediate-next-review floor fail on plan-adherence dimension** after the constraint was injected — reactive quarantine.
3. **Fallback: third-agent semantic check** — only for same-scope ambiguity neither rule above catches. Expensive; used sparingly.

## Constraint → writer directive mapping (what can be learned vs plan-revised)

| Category | Writer-addressable | Route to plan-revision |
|---|---|---|
| Forbidden lexicon / calques (`приймати→брати участь`) | ✓ | |
| Register / pronoun rules per speaker | ✓ | |
| Required dialogue acts (`А у тебе?`) | ✓ | |
| Typographical / notation fixes (`[=]` notation) | ✓ | |
| Context-free aspect / paronym / stress rules | | ✓ |
| Vocabulary density / mandatory list scope | | ✓ |
| Pedagogical sequence of sections | | ✓ |
| Plan-level register contradiction | | ✓ |
| Scenario ↔ grammar alignment | | ✓ |

If a normalized finding maps to a plan-revision category, the ladder SHOULD bias toward tier 5 faster (don't waste full_rewrite on it).

## --force semantics

**Current state (before this spec):** `_clean_build_artifacts()` (`v6_build.py:954`) only preserves `index.md` + `friction.yaml`. `--force` would DELETE `module-memory.yaml` today. This is a spec-required code change, not just policy.

**After this spec:**
- `--force` → wipes chunks, dispatches, review rounds, contracts. **Preserves** `module-memory.yaml`. Requires explicit addition to preserve list in `_clean_build_artifacts()`.
- `--force --reset-memory` (new flag) → also wipes `module-memory.yaml`. Used for corrupted constraints or post-plan-revision lineage cuts. Must be wired through BOTH single-module path AND `--range` child invocations (`v6_build.py:9399`).
- **Plan-hash mismatch at boot** → auto-clears `constraints` block (keeps `history` for audit), logs `plan_hash_invalidation` event.

## Terminal states

```
pass                       → publish
plan_revision_request.yaml → HUMAN TERMINAL. Structured proposal:
                             {dimension, persistent_finding, suggested_plan_edit}.
                             User approves → plan version bumps → pipeline
                             restarts with cleared constraints + fresh plan_hash.
budget_exhausted.yaml      → HUMAN TERMINAL. Emits full history trail for
                             diagnosis. User decides: extend budget / force
                             plan revision / abandon.
```

**Terminal-state migration is broader than deleting one emission site.** `needs-human-review.yaml` is baked into:
- emission (`v6_build.py:10106`)
- state cleanup (`v6_build.py:1219`)
- contradiction checks (`v6_build.py:1256`)
- state flag reads (`v6_build.py:10028`)

All four must be replaced atomically — the `state["needs_human_review"]` contract migrates to `state["terminal"]` with values in `{"pass", "plan_revision_request", "budget_exhausted"}`. Otherwise resume/consistency logic drifts and old-flag readers race new-flag writers.

## Downstream invalidation discipline

Every tier that regenerates prose (section_rewrite, full_rewrite, writer_swap) MUST refresh the full sidecar chain:

```
annotate → activities → repair → verify → verify-exercises → vocab
```

Not just activities + vocab (v3 undersold this). Precedent: `_refresh_post_patch_sidecars` (`v6_build.py:8590-8603`).

**Sidecar validation against plan**: sidecar regeneration must validate output against plan requirements (mandatory vocab list, required activity types, word count target per section). Not just "extract what writer produced." Fails loudly on missing mandatory items.

## Constraint hierarchy

Module-level constraints (`module-memory.yaml`) override track-level constraints (`learned-constraints-track.yaml`) in prompt assembly. Explicit `override_track_level: true` flag; logged on every injection for audit.

## Track-level promotion (phase C)

Promotion bar (all required):
- Normalized constraint ID appears in ≥ 8 modules × ≥ 2 levels with `status: active`
- Zero `conflicts_with_plan` across those modules
- Measured improvement after rollout, defined as ALL of:
  - Statistically significant increase in **Attempt-0 first-review pass rate** across ≥ 5 post-rollout modules
  - Reduction in hard-floor failures on the target dimension
  - Reduction in recurrence of the specific normalized finding on Attempt 0

Promotion ≠ overall score delta. Overall score masked real problems in the A1 macro report (`shopping` 10/10 overall / 5/10 dialogue).

## Success criteria

Pipeline health = rate of honest human terminals, split:
- **`budget_exhausted` → near-zero steady state** (≥ 99% of modules exit via `pass` or `plan_revision_request`)
- **`plan_revision_request` → 3-5% healthy floor** (plans are human-authored; some will be flawed once expanded)
- **`needs-human-review.yaml` → 0** (removed from codebase)

Success is "zero fake autonomy + shrinking human-terminal rate", not "zero human terminals."

## Implementation plan — ship everything together

Single implementation pass, ~800 LOC total (revised up from 700 after topology classifier + preserve/reset plumbing + state contract migration). Delegated to Codex. **One end-to-end adversarial review round after implementation complete, before merge.** Test on the stuck A1/M1 `sounds-letters-and-hello` module as the motivating convergence case.

### Deliverables (all in one pass)

**New modules:**
- `scripts/build/module_memory.py` — schema, load/save, plan-hash invalidation, `--reset-memory` plumbing
- `scripts/build/finding_normalizer.py` — hand-written enum + lookup tables, `unclassified` fallback, growth log
- `scripts/build/finding_topology.py` — deterministic `local_to_prose`/`section_local`/`cross_section`/`plan_level` classifier
- `scripts/build/convergence_loop.py` — replaces `_run_review_heal_loop`. Tier selection, hard-floor priority reorder, stall signals, terminal emission, sidecar refresh orchestration.
- `scripts/build/track_constraints.py` — track-level promotion pipeline, override precedence, base template assembly

**Modified:**
- `v6_build.py:954` — `_clean_build_artifacts()` preserves `module-memory.yaml` by default
- `v6_build.py:9399` — `--range` child invocations propagate `--reset-memory`
- `v6_build.py:1219, 1256, 10028, 10106` — replace `state["needs_human_review"]` contract with `state["terminal"]` across cleanup / contradiction checks / reads / emission
- `v6_build.py:4855` — `_determine_reviewer()` honors `CONVERGENCE_MATRIX_ENFORCED` feature flag
- `v6_build.py:8590-8603` — generalize `_refresh_post_patch_sidecars` to full chain (`annotate → activities → repair → verify → verify-exercises → vocab`), add plan-requirements validation
- `audit/checks/review_gaming.py:675-683` — no change (flag gates in `_determine_reviewer`, audit stays warning-level)

**Removed:**
- `needs-human-review.yaml` emission path (replaced by `plan_revision_request.yaml` / `budget_exhausted.yaml`)
- `_run_review_heal_loop` (replaced by `_run_convergence_loop`)

**Generated files (runtime):**
- `orchestration/{slug}/module-memory.yaml`
- `orchestration/{slug}/plan_revision_request.yaml` (on tier 5 terminal)
- `orchestration/{slug}/budget_exhausted.yaml` (on 5-attempt cap hit)
- `curriculum/l2-uk-en/stuck-modules.yaml` (single-pane aggregator, Monitor API-consumable)
- `curriculum/l2-uk-en/learned-constraints-track.yaml` (populated after track promotion pipeline runs)

### Test suite (required before review gate)

- Unit: schema round-trip, plan-hash invalidation, conflict detection true/false positives, `--reset-memory` behavior, normalizer deterministic output, topology classifier deterministic output
- Integration: each tier triggers correctly on synthetic findings; hard-floor priority correct; terminals emit with structured payload; sidecar refresh invokes full chain + plan validation catches missing mandatory items
- End-to-end: **stuck A1/M1 `sounds-letters-and-hello` converges to `pass` OR hits `plan_revision_request` within 5 attempts.** This is the motivating case; if it hits `budget_exhausted`, the design needs another look.
- Regression: running convergence loop on a previously-passing A1 module produces identical output (tier 1 patch or immediate pass)

### Single review gate (before merge)

Gemini + Codex adversarial on complete implementation. No merge until both approve and end-to-end test on stuck module succeeds.

## Resolved (from final review round)

1. **Finding normalization** → hand-written enum (15-20 initial error classes: `calque`, `register_drift`, `surzhyk`, `missing_vocab`, `stress_error`, `notation_error`, `dialogue_arc_fail`, etc.). `unclassified` fallback grows the table over time from logged unclassified findings.
2. **`sources_hash`** → content-hash manifest (NOT mtimes): VESUM lemma+form tables, FTS5 textbook/literary/dict indexes, Правопис file contents, wiki packet for slug, base writer template.
3. **Reviewer matrix** → `CONVERGENCE_MATRIX_ENFORCED` feature flag, default OFF. Flipped ON when cross-agent review capacity returns. Self-review allowed under OFF (today's behavior); tier 5 escalation on reviewer-unavailable under ON.
4. **`plan_revision_request.yaml` format** → structured `{dimension, persistent_finding_id, proposed_plan_edit_summary}`. Not a diff; plan stays human-authored source of truth.
5. **`stuck-modules.yaml`** → single-pane aggregator at `curriculum/l2-uk-en/stuck-modules.yaml`, consumed by Monitor API `GET /api/state/failing`. Both terminals (`plan_revision_request` + `budget_exhausted`) append.

(Artifacts + file changes listed under "Deliverables" above.)
