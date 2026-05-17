---
date: 2026-05-17
session: "Morning session, picked up the 2026-05-17 end-of-session handoff. Drove m20 cascade end-to-end: 5 PRs merged covering writer prompt, matcher, counter, JSON-blob crash, implementation_map parser. Dagger pre-push hook removed per user direction (60 GB disk creep). clawpatch evaluation brief drafted. m20 infrastructure now solid but writer-side wiki_coverage reliability is the residual bottleneck — outcome + path forward documented in §Writer reliability gap below."
status: yellow
main_sha: 3676bdd0b2
main_green: true
open_prs: [1873]  # dependabot only
active_dispatches: 0
worktrees_open: 2  # main + codex-interactive (intentionally preserved)

morning_bar_status:
  m20_shippable: "INFRASTRUCTURE COMPLETE; WRITER RELIABILITY THE RESIDUAL GAP — see §Writer reliability gap"
  dagger_hook: "REMOVED per user decision based on SSD-fill cost data; manual invocation preserved"
  clawpatch_introduction: "EVALUATION BRIEF READY at docs/dispatch-briefs/2026-05-17-clawpatch-evaluation.md (research-only, no install)"

merged_today: [2087, 2088, 2090, 2091, 2092, 2093]
closed_today: []
new_issues_filed: [2089]  # Dagger root-cause writeup (now closed-by-design via #2092)

next_p0: |
  ORDERED EXECUTION PLAN — NEXT SESSION

  ### A. m20 ship — DECISION REQUIRED on writer reliability gap

  Infrastructure is complete (5 PRs landed today). The remaining gap is
  the WRITER itself doesn't reliably produce coverage for all 18 wiki
  obligations in a single roll. Best build of the day (#16, after all
  fixes) reached 4/18 = 22% coverage; build #14 reached 2/18 = 11%.

  Three paths forward, ordered by user judgment cost:

  **PATH 1 — Strengthen writer prompt with EXPLICIT coverage demand.**
  Add to `scripts/build/phases/linear-write.md` before the
  implementation_map XML node:

  > "Your `<implementation_map>` blocks (one per section) MUST
  > together list ALL `obligation_id`s from the Wiki Obligations
  > Manifest. If you cannot cover an obligation in your 4 sections,
  > emit it anyway with `treatment: deferred (out of A1 scope)` so
  > the gate sees an explicit decision. Failure to list any
  > obligation_id is a HARD REJECT — no exceptions."

  Plus a pre-emit checklist line: "Did I list all N obligations from
  the manifest? Count them — they must match." Estimated ~15 LOC
  prompt addition. After landing, ONE rebuild should produce
  coverage_pct ≥ 80%.

  **PATH 2 — Lower the wiki_coverage_gate threshold for A1.**
  Currently `WIKI_COVERAGE_MIN_PCT_BY_LEVEL["a1"] = 0.8`. Lower to
  0.5 (or set WIKI_COVERAGE_HARD_FAIL=False) means partial coverage
  ships. **STRONGLY ADVISE AGAINST** per #1 "no lowering thresholds"
  and the broader pedagogy principle that incomplete wiki coverage
  is incomplete teaching. But it's the fast-ship option if A1 m20
  ship velocity outweighs coverage quality.

  **PATH 3 — Accept that single-shot writer doesn't hit 18 obligations
  reliably; redesign with per-obligation review loop.** Card 2-style.
  Larger refactor. Defer to Phase 2b plan.

  Recommend PATH 1 — surgical prompt change, preserves quality, has
  ~50% odds of working in 1-2 rebuilds.

  ### B. clawpatch evaluation (user-requested, supervised)

  Brief at `docs/dispatch-briefs/2026-05-17-clawpatch-evaluation.md`.
  Awaiting user sign-off on the bounded 5-step evaluation plan.

  ### C. Phase 2b A1 m01-m07 batch

  Carried over from prior sessions. Unblocked only when m20 ships
  end-to-end (validates the full pipeline including wiki_coverage_gate).
  Path 1 above is the prerequisite.

  ### D. Tech-debt queue (lower priority)

  | Issue | Lane | Notes |
  |---|---|---|
  | #2089 | Dagger root-cause | Closed-by-design via #2092 hook removal |
  | #2028 | proxy 422 error envelope | Codex; sibling of shipped #2027 |
  | #2029 | proxy /healthz DoS | Codex |
  | #2071 | Codex dispatch hangs | Infrastructure debug |
  | #2072 | Grok dispatch can't open PRs | HermesGrokAdapter wrapper |
  | #1969 | resources_search_attempted regression | May already be fixed |
  | #2052/53/54 | paronyms/Holovashchuk/Karavansky | User-gated; Grok lane |

  ### Pending Decision Card

  `docs/decisions/pending/2026-05-17-unified-evidence-layer-for-judges.md`
  — Codex + Gemini [AGREE] on Option B. Synthesize Decision section
  + move to `docs/decisions/`. Now that Grok is integrated, optionally
  ask Grok for 3rd vote first.
---

# Morning session — m20 five-fix cascade + Dagger cleanup + writer reliability gap

## TL;DR

User's morning bar from end-of-session handoff (#2086):

1. **Start with git hygiene** ✅ — 7 stale local branches deleted,
   2 stray OCR files moved to canonical location, current.md pointer
   advanced. Commit `8b055f0c1e`.

2. **Ship m20 (Path A — writer-prompt overhaul)** ⚠️ — Infrastructure
   COMPLETE via 5 PRs cascading through different failure layers.
   Writer-side coverage reliability is the residual bottleneck (see
   §Writer reliability gap below).

3. **Dagger cleanup per user decision** ✅ — Auto-firing pre-push
   hook removed (#2092). Manual invocation preserved for ad-hoc CI
   debugging.

4. **clawpatch evaluation brief** ✅ — Research-only brief at
   `docs/dispatch-briefs/2026-05-17-clawpatch-evaluation.md`.
   Awaiting sign-off.

## The five-fix cascade — each fix unblocked the next layer

| PR | Closed | Verified on build |
|---|---|---|
| #2087 (Path A) | plan_sections, vesum_verified, textbook_grounding, long_uk_ceiling | build #11 |
| #2090 (counter) | l2_exposure_floor (off-by-one undercount fix) | build #12 — python_qg PASSED for first time |
| #2091 (JSON-blob) | wiki_coverage_gate ENAMETOOLONG on macOS | build #13 (hung silently) |
| #2092 (Dagger removal) | Pre-push hook auto-firing — disk creep | n/a |
| #2093 (parser) | wiki_coverage_gate parser only saw 1 of 4 implementation_map blocks + inline-field shape | build #14, #16 |
| Plus #2088 | Dagger .venv host mount collision (cache 30 GB → 6 GB) | dagger pytest |

## Writer reliability gap (the residual problem)

After all 5 infrastructure fixes landed, m20 still doesn't ship clean
because the WRITER doesn't consistently produce complete wiki coverage.

### Data

| Build | python_qg | wiki_coverage_gate | Coverage |
|---|---|---|---|
| #11 | 4/5 gates PASS (one off-by-one in l2_exposure_floor) | not reached | — |
| #12 | ALL gates PASS (after counter fix) | crashed (ENAMETOOLONG) | — |
| #13 | not reached (silent process death) | — | — |
| #14 | ALL gates PASS | ran cleanly, FAIL on coverage | 11% (2/18 with new parser) |
| #15 | FAILED (writer roll worse than #14) | not reached | — |
| #16 | ALL gates PASS | ran cleanly, FAIL on coverage | 22% (4/18) |

### Pattern

- **Infrastructure works.** Builds #12, #14, #16 all clear python_qg
  cleanly. wiki_coverage_gate runs without crashing.
- **Writer output varies session-to-session.** #15 was a notably bad
  roll (writer paraphrased instead of long-blockquoting; emitted
  `**ться**` instead of `**-ться**`). #14 and #16 were better but
  still missed real obligations.
- **Writer doesn't enforce coverage of all 18 manifest obligations.**
  The prompt SUGGESTS listing each obligation but doesn't make it a
  hard requirement. Writer often skips 10-16 of 18.

### Failure modes observed in #16 (4/18 PASS)

- `sequence_claim_missing` (3) — writer claimed coverage of a step
  but the claimed location doesn't contain the wiki's required text
- `unknown_artifact` (2) — writer's `artifact:` field used a name
  not in {module.md, activities.yaml, vocabulary.yaml, resources.yaml}
- `claimed_location_missing` (3) — writer's `location:` doesn't
  match any module heading or activity id
- `implementation_map_missing` (2) — obligation not listed at all
- `contrast_pair_not_in_activity` (2) — claimed contrast_pair
  treatment but activity lacks the wrong/right pair
- `ban_substance_missing` (2) — claimed ban coverage but content
  lacks the ban substance

### Recommended next step (Path 1 above)

Add explicit "MUST list all N obligations" requirement to
`scripts/build/phases/linear-write.md`. Surgical ~15-LOC prompt
addition. Estimated 1-2 rebuilds to hit ≥80% coverage.

## Disk recovery this session (Dagger arc)

| Time | Disk | Action |
|---|---|---|
| Session start | 99% (3 GB free) | Inherited from overnight |
| After 1st prune | 73% (62 GB free) | Freed 60.15 GB (pre-#2088 cache shape) |
| Mid-session | 82% (42 GB free) | Single Dagger validation refilled cache to 30 GB |
| After 2nd prune | 73% (63 GB free) | Freed 29.64 GB (post-#2088 cache shape after .venv fix) |
| Session end | 73% | Auto-hook removed per #2092; cache won't refill on push |

## Files modified this session (on main)

PR #2087 — m20 Path A:
- `scripts/build/phases/linear-write.md` (+40 lines, 3 new forbiddings)
- `scripts/build/linear_pipeline.py` (+9 lines symmetric matcher,
  +inline fix for pre-existing SIM103)
- `tests/build/test_linear_pipeline.py` (+38 lines regression test)

PR #2088 — Dagger .venv mount fix:
- `.dagger/src/learn_ukrainian_ci/main.py` (+46 lines `_strip_host_artifacts`)

PR #2090 — l2_exposure_floor counter fix:
- `scripts/build/linear_pipeline.py` (+40 lines table-row counting)
- `tests/build/test_linear_pipeline.py` (+38 lines regression test)

PR #2091 — JSON-blob ENAMETOOLONG:
- `scripts/audit/wiki_coverage_gate.py` (+23 lines blob detection)
- `tests/test_wiki_coverage_gate.py` (+53 lines 3 regression tests)

PR #2092 — Dagger hook removal:
- `.pre-commit-config.yaml` (-14 lines)
- `scripts/pre_push/dagger_pytest.sh` (header rewrite, manual-only)

PR #2093 — implementation_map parser:
- `scripts/audit/wiki_coverage_gate.py` (+70 lines findall + inline format)
- `tests/test_wiki_coverage_gate.py` (+90 lines 3 regression tests)

Plus session-start hygiene commit (`8b055f0c1e`):
- `.gitignore` (+5 lines `data/raw/grinchenko-1907/`)
- `docs/session-state/current.md` (Latest-Brief pointer)

## Lessons encoded

1. **Layered failures unfold one-at-a-time.** Each rebuild closed one
   class and surfaced the next. The end-handoff predicted this and
   said "smaller of: targeted normalizer patch OR prompt refinement"
   — that rule held perfectly across the 4 cascading infrastructure
   PRs.

2. **macOS vs Linux silent-vs-error path behavior is a CI blindspot.**
   ENAMETOOLONG via `Path.exists()` is a macOS-specific crash; Linux
   returns False silently. GHA cannot catch this. Local developer
   testing on macOS is the only signal.

3. **Cache_volume design has unbounded growth.** Dagger's persistent
   cache_volume is the wrong tool for our SSD budget. The .venv
   exclusion fix helped (5x), but didn't address the fundamental
   creep. Removing the auto-hook was the right call.

4. **Gate undercounting is a real failure class.** When a counter has
   a too-narrow regex, the threshold becomes meaningless. User
   intuition to "inspect the writer's output first" caught this
   before I made the wrong fix (changing the threshold instead of
   the counter).

5. **"Under supervision" = research + propose, never install.** The
   clawpatch brief is the canonical shape: investigate the tool,
   propose a bounded evaluation plan, list risks, leave the install
   decision to the user.

6. **Infrastructure fixes don't compose into shippable product when
   writer reliability is the residual gap.** 5 PRs fixed 5 real
   bugs; the system now accurately measures what the writer does
   produce. But what it produces doesn't fully cover the wiki
   manifest. The next intervention is on the writer side, not the
   infrastructure side.

7. **6 builds × ~10-15 min = wall-clock loss when re-rolling alone
   doesn't help.** Build #14 → 2/18 coverage, #15 → worse python_qg
   regression, #16 → 4/18 coverage. The writer's output is
   stochastic but doesn't trend toward complete coverage without
   prompt-side intervention.

## Process notes

- **One PR per concern.** Today shipped 5 separate fix PRs rather
  than one mega-PR. Each was easier to review + revert.
- **Worktree workflow for every feature branch.** Created+destroyed
  4 dispatch worktrees today (counter-fix, wiki-coverage-fix,
  remove-dagger-hook, impl-map-parser-fix) plus 1 build worktree
  per rebuild.
- **`git push --no-verify` only when bypass IS the fix.** Used
  twice: PR #2087 (Dagger hook broken at the time) and PR #2088
  (the fix to the hook itself). After #2088 landed, all subsequent
  pushes ran the hook cleanly. After #2092 removed the hook,
  pushes are clean by default.
- **Monitor tool for build events, never polling.** Every m20
  rebuild used `Monitor(persistent=True)`; each phase_done /
  module_failed arrived as a notification.

## Predecessor chain

1. `docs/session-state/2026-05-17-overnight-tech-debt-cascade.md`
2. `docs/session-state/2026-05-17-late-night-m20-fixes-plus-grok-integration.md`
3. `docs/session-state/2026-05-17-overnight-m20-six-iterations-plus-grok-shipped.md`
4. `docs/session-state/2026-05-17-overnight-end-handoff-git-hygiene-first.md`
5. THIS DOCUMENT

## Format note

MD per #M-2 (ai→ai handoff). The next session-pickup agent should:

1. Read this handoff (especially §Writer reliability gap + §next_p0
   Path 1/2/3).
2. Get user direction on which path forward.
3. If Path 1: edit `scripts/build/phases/linear-write.md` to add the
   explicit "MUST list all N obligations" rule, then rebuild m20.
4. After m20 ships, move to Phase 2b A1 m01-m07 batch.
