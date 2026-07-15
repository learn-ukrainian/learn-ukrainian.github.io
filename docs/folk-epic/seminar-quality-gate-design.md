# Seminar Content-Quality Gate — Design & Execution Plan

> **Status:** DESIGN LOCKED (2026-06-17, user-aligned). Prototype on **folk** (6 built
> modules), then regroup before rolling to every seminar track (hist · bio · istorio ·
> lit · oes · ruth). Author: Claude folk-track driver. This is the load-bearing spec —
> a fresh session executes from here.

## 0. Core principle — AGENTS IN TANDEM > the best solo model (user 2026-06-17)

> **2026-06-23 supersession note:** §9 supersedes the model PANEL idea as the
> gating mechanism for PR1. A panel remains a future option; the locked MVP gate
> is one recorded cross-family reviewer bound to the exact content hash.

> *"Agents working in tandem surpass the most advanced LLM model. We have to stick to this."*
> Proven in-house this very session: Codex (a different model) found **3 real holes** in the
> liveness gate that my own (Claude) review missed. Tandem catches what solo cannot.

This is the methodology's spine, not a nicety. It applies in **three** concrete ways:

1. **Writing = ensemble bake-off.** Multiple fleet writers (claude / codex / agy / cursor /
   grok) draft the same module/wiki; the best advances (or we merge best-of). Never a
   single writer for content that must be beautiful.
2. **Verification = cross-model, adversarial.** Every module/finding is checked by a
   *different* model than wrote it (deepseek high-volume; codex green-team). Self-review is
   the weakest link; the `SELF_REVIEW_DETECTED` gate already forbids same-model review.
3. **The gate itself = a model PANEL, not one reviewer.** ← This is the key insight: the
   subjective dims (beauty/engagement/pedagogy) were demoted in May 2026 because a *single*
   reviewer scored them too noisily. **A panel (e.g. deepseek + codex + agy + claude) scoring
   each dim, aggregated by median/majority, collapses that variance** — making the SOLE-judge
   gate trustworthy precisely because no single model is the judge. Tandem solves the noise
   that solo created. Build the gate this way.

Everything below serves this principle.

## 1. Why this exists

`verify_shippable` only proves *machine correctness* (renders, valid VESUM words, real
links). It does **not** measure whether content is **good teaching, engaging, or
beautiful**. The separate LLM-QG review *does* score those, but on 2026-05-23 the
subjective dims (pedagogical/naturalness/engagement/tone) were demoted to **warning-only**
(`LLM_QG_TERMINAL_DIMS = {decolonization}`) because noisy scoring blocked every module
("0 shipped across 6 builds"). Net effect today: **weak content ships** — folk modules sit
at pedagogical 5.8–7.0, engagement 6.8–7.4 yet pass.

The user's mission: *proper, enjoyable content about the beauty of Ukrainian folk
literature that upheld identity through centuries of oppression.* The gate must **enforce**
that, autonomously.

## 2. User-aligned decisions (2026-06-17 interview)

| # | Decision |
|---|----------|
| Beauty | New `beauty` dim rewards **BOTH** craft (vivid, elegant, memorable lesson prose) **AND the source's soul** — real folk texts (songs/dumas/laments) quoted and framed so their beauty + identity-bearing power *resonates*. Lean toward conveying the source. |
| Learner | **Fall in love with the heritage (primary) + advanced Ukrainian practice (primary), academic depth woven in where it deepens interest.** Near-full Ukrainian immersion (seminar standard 98–100%). Not dry scholarship; not a drill. |
| Judge | **LLM gate is the SOLE judge** — fully autonomous, no human sign-off. ⇒ rubric must be precise + low-noise; correction loop must converge or nothing ships. |
| Scope | **Prove on the 6 built folk modules** (→ ≥8 on the 3 dims, live, finished wikis+dossiers, reusable gate). **Then regroup** before other tracks. |
| Dimensions | Add **`beauty` only.** `pedagogy`=pedagogical, `enjoyability`=engagement (sharpen rubric, don't duplicate). 6 total: pedagogical, engagement, beauty, naturalness, decolonization, tone. No proliferation — extra dims re-create the 2026-05-23 noise failure. |
| Cost | **Nothing is free.** deepseek cheapest; gemini/agy no longer cheap. **Quality > cost.** Use the WHOLE fleet by fit. |
| **Flexibility** | **The dimension emphasis is PER-TRACK, NOT hardwired** (user 2026-06-17). Folk/lit lean *beauty*; hist/istorio lean *rigor/history*; bio its own balance. The 6 dims are a universal palette; each track configures which are emphasized, their floors, and which gate. Must be **data-driven + flexible**, never one-size-fits-all. |

## 2a. Per-track flexibility — the BACKBONE principle (NOT hardwired)

> User 2026-06-17: *"sometimes we want to be more beauty oriented, sometimes more history
> oriented. It is not hardwired. We have to be flexible."* This is the core of the reusable
> methodology — the whole point of prototyping on folk before other tracks.

The **6 dimensions are a universal palette** (pedagogical, engagement, beauty, naturalness,
decolonization, tone). What varies **per seminar track** is a **dimension PROFILE**:

- **which dims gate** (terminal) for that track,
- **the per-dim `pass_floor`** (emphasis = a higher floor; de-emphasis = a lower-but-present floor — never zero, so quality never silently drops),
- optional per-dim **weighting** if we move beyond MIN aggregation.

Illustrative (to be tuned, not final):

| Track | Beauty | Pedagogy | Engagement | Decolonization | Rigor/accuracy lens | Emphasis |
|-------|--------|----------|------------|----------------|---------------------|----------|
| folk / lit | gate ≥8 (high) | gate ≥8 | gate ≥8 | gate ≥9 | present | **beauty + heritage-love** |
| hist / istorio | present ≥7 | gate ≥8 | gate ≥8 | gate ≥9 | **gate, high** | **rigor + decolonized accuracy** |
| bio | gate ≥8 | gate ≥8 | gate ≥8 | gate ≥9 | gate | balanced narrative + accuracy |
| oes / ruth | per their pedagogy | gate ≥8 | gate ≥8 | gate ≥9 | gate | source-faithful |

**Implementation:** keep it **data-driven** — a per-track profile table (extend the
existing per-profile mechanism: `terminal_dims_for(profile)` + per-track floor overrides in
`scripts/audit/config.LEVEL_CONFIG` or a dedicated `TRACK_DIM_PROFILES` map in
`thresholds.py`). Adding/retuning a track = a config edit, **never** a code rewrite. Folk's
profile is the first concrete instance; the others are filled in as each track is built.

If "rigor/accuracy" proves it needs to be its own scored dimension (distinct from
decolonization) for history-leaning tracks, that's the sanctioned 7th dim — but add it only
when a track's profile demands it, and keep MIN-aggregation noise in mind (§3).

## 3. The gate change (Phase A)

> **2026-06-23 supersession note:** §9 supersedes this phase for the gating
> mechanism. Do not re-arm in-build LLM-QG terminal dims; enforce quality at the
> promote boundary through the deterministic recorded sidecar.

**Make `pedagogy + engagement + beauty` gating at ≥8 — but for SEMINAR profiles ONLY.**

Critical: `terminal_dims_for(profile)` already splits core vs seminar (core →
`frozenset()`; seminar → terminal set). **Scope the new terminal dims to seminars** so
CORE tracks (a1–c2, owned by Codex) are untouched — no breaking change, no cross-owner
coordination needed.

Touchpoints:
- `scripts/common/thresholds.py`:
  - `QG_DIMS` += `"beauty"`.
  - `_make_review_floors(...)` += `beauty` param; add `beauty=8.0` to all 7 call sites
    (A1,A2,B1,B2,C1,C2,_DEFAULT). The `LevelThresholds.__post_init__` invariant *forces*
    this — good, it fails closed if a level is missed.
  - Promote `pedagogical, engagement, beauty` to terminal **for seminar profiles**: extend
    the seminar branch of `terminal_dims_for` (NOT `LLM_QG_TERMINAL_DIMS` globally). Keep
    core's `frozenset()`. Decolonization stays terminal everywhere.
  - Update the 2026-05-23 rationale comment: re-promotion is justified by (a) the
    correction loop now closing the gap and (b) seminar-scoped blast radius.
- **Reviewer rubric** `agents_extensions/shared/phases/gemini/_shared-quality-dimensions.md`
  (+ check `v6-review.md`, `phase-5-review.md`, `review-structured.md`,
  `phase-D1-structured-review.md`): ADD the `beauty` dimension with a concrete craft+soul
  rubric; SHARPEN `engagement`→ enjoyment / "fall in love with the heritage"; SHARPEN
  `pedagogical`→ the advanced-immersion seminar learner. The reviewer MUST emit a `beauty`
  score or the dim is silently skipped by `aggregate_review`.
- **Noise mitigation (sole judge!) — via §0 tandem panel, not a single reviewer:** the
  subjective dims (beauty/engagement/pedagogy) are scored by a **PANEL of models** (deepseek
  + codex + agy + claude) and aggregated by **median/majority** — this is what makes a SOLE
  autonomous judge trustworthy and is the direct fix for the May 2026 single-reviewer noise
  that demoted these dims. Each panellist gives concrete 8-vs-6 anchors + a falsifiable
  evidence quote (already required by the reviewer-evidence gate). Implementation: the QG
  review step fans out to N models and `aggregate_review` consumes the per-dim median.
- **Tests:** `tests/test_threshold_source_of_truth.py` (QG_DIMS count), any dim-count
  asserts, + new tests: seminar profile gates on beauty/engagement/pedagogy <8; core
  profile does NOT; beauty floor present on every level.

**Do NOT merge Phase A piecemeal:** terminal promotion + reviewer-emits-beauty +
correction-loop-converges must land coherently, or seminar builds fail with no path to
pass.

## 4. De-risk FIRST (Phase B) — the #1 risk

Because the gate is **sole judge**, the 2026-05-23 "nothing converges/ships" failure is the
top risk. **Before** the foundation sweep: prove the build + correction loop (#3079) drives
ONE folk module from its current weak score to **≥8 on beauty/engagement/pedagogy**, using
its existing wiki/dossier. If it can't converge, fixing the loop is priority #0.

## 5. Foundation then rebuild (Phases C–D), fleet-orchestrated

- **C. Finish the 6 modules' wikis + dossiers** (`wiki/folk/...`, `docs/research/folk/...`).
- **D. Rebuild the 6 modules → ≥8**, one at a time, grounded in C.

### Fleet utilization (user directive 2026-06-17 — use the WHOLE fleet by fit)

| Role | Agents | Notes |
|------|--------|-------|
| Module/wiki/dossier WRITERS (bake-off → pick best per item) | claude-tools, codex-tools, agy(gemini), cursor, grok, grok-4.* | Maximize quality via multi-writer bake-off; the gate scores all, best advances. |
| High-volume REVIEW | **deepseek** (cheapest) | Routine content/code review. |
| Adversarial / green-team | codex | Hole-hunting (it caught 3 real holes in the liveness gate this week). |
| Taste / architecture / final judgment-in-the-loop | claude (in-session, me) | Design + spot-checks; NOT a headless claude reviewer (quota). |
| Automated SOLE judge | LLM-QG gate (the thing we're building) | The ship arbiter. |

Cost note: nothing is free; route cheap (deepseek) where it doesn't cost quality; spend
freely on quality where it matters. This is explicit multi-agent orchestration — a
`Workflow` (writer bake-off → gate → deepseek/codex review → best advances) fits Phase D.

## 6. Known structural blocker for the mission

**#3162** — folk *literary* primary texts (the songs, dumas, laments) are **not embedded /
searchable**; the writer pulls from textbooks, not the literary corpus. For "beauty of folk
literature," this is foundational: without it, lessons can't reach into the real corpus to
quote it beautifully. Resolve as part of Phase C (ingest/route the folk literary corpus +
a non-word-counted primary-text reading panel).

## 7. Current folk state (verified 2026-06-17, not from stale handoff)

- 42 topics planned; **6 modules built**; **20 folk wikis**; **26 folk dossiers**.
- **5/6 pass `verify_shippable`** (machine gates) after #3428's liveness-gate fix:
  kalendarna, koliadky, narodna-kultura, narodni-viruvannia, zamovliannia. dumy fails on
  one compound word `татаро-турецькі` (vesum hyphenated-compound false positive).
- **Folk is ALREADY live & surfaced** (homepage "Folklore" card + `/folk/...` routes 200).
  So the work is quality, not surfacing. The deployed kalendarna page is slightly stale vs
  its corrected source (deferred MDX regen + a generator discrepancy: char-split rubric +
  richer prompt — investigate before re-deploying).
- LLM-QG content scores (the gap this whole effort closes): pedagogical 5.8–7.0,
  engagement 6.8–7.4, decolonization 7.8–9.5 (lens good, craft weak).

## 8. Execution order (for the fresh session)

0. Phase B de-risk (1 build) — prove the loop converges on one module.
1. Phase A gate (rubric + thresholds + seminar-scoped terminal + tests), coherent, reviewed by codex+deepseek.
2. Phase C foundation: #3162 literary-corpus routing + finish 6 wikis + 6 dossiers (fleet writers, deepseek review).
3. Phase D: rebuild 6 modules → ≥8 (fleet bake-off workflow + gate + correction loop), one at a time.
4. Phase E: verify 6 live ≥8, regen MDX (resolve generator discrepancy), REGROUP for user judgment → then generalize to all seminar tracks.

## 9. Option A — deterministic PRE-PROMOTE gate (LOCKED 2026-06-23, supersedes §3)

The May-2026 demotion of subjective LLM-QG dimensions is permanent for in-build
behavior. Do **not** re-arm `QG_DIMS`, `aggregate_review`,
`terminal_dims_for`, or `v7_build.py` LLM-QG enforcement. The in-build reviewer
continues to warn on subjective dimensions so the build loop does not recreate
the 2026-05-23 "0 ships" failure.

Quality is enforced separately at the promote boundary. A seminar module may
promote only when it has a git-tracked `promote_quality.json` sidecar next to
`llm_qg.json`, containing a recorded cross-family LLM-QG score that is bound to
the exact lesson source content hash. The hash basis is `lesson_sources_v1`:
the source plan plus `module.md`, `activities.yaml`, `vocabulary.yaml`, and
`resources.yaml` when present.

The mechanism components are:

- `scripts/common/thresholds.py`: source of truth for per-track promote floors
  via `SEMINAR_PROMOTE_DIMS`, `SEMINAR_PROMOTE_PROFILES`, and
  `seminar_promote_floors_for`.
- `scripts/build/promote_quality_gate.py`: deterministic `record` and `verify`
  tool. `record` computes hashes from disk and stamps current floors; `verify`
  fails closed on missing, stale, same-family, unknown-family, barred reviewer,
  below-floor, missing-dimension, or weaker-recorded-floor sidecars.
- `scripts/build/verify_shippable.py`: adds a `promote_quality` step after the
  existing render/build checks. Unenrolled levels are non-blocking `n/a`; enrolled
  tracks fail shippability when the sidecar is absent or invalid.
- `scripts/sync/promote_module.py`: PR1 includes only the missing `json` import
  bug fix for the folk readings promote path. The actual promote hook remains
  PR2 scope.
- `tests/test_promote_quality_gate.py` and
  `tests/test_threshold_source_of_truth.py`: cover the fail-closed sidecar
  behavior and keep the threshold floors in the SSOT.

MVP reviewer policy is a single cross-family reviewer. A second review is an
appeal or audit path, not a default blocker. For folk, DeepSeek is barred as the
promote-quality reviewer in code. Enrollment is folk-first and per-track:
adding another seminar track is a thresholds profile entry plus tests, not an
in-build LLM-QG behavior change. PR1 is mechanism only; CI enforcement,
`promote_module.py` gate wiring, sidecar bootstrap, and required-check governance
belong to PR2.
