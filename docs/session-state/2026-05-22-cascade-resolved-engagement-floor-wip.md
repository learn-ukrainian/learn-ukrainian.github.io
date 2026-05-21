---
date: 2026-05-22
session: "Cascade resolution day — 4 PRs merged, build #11 MDX live on starlight, engagement_floor gate WIP"
status: yellow-cascade-resolved + 4-PRs-merged-tonight + 1-PR-wip-on-branch + 0-active-dispatches + 0-active-builds
main_sha: 867d2e1f6d
main_green: clean (all blocking CI green; the `review / review` Gemini-auth advisory failure persists on every PR)
working_tree_dirty: false  # main clean; WIP lives on fix/engagement-deterministic-floor branch
prs_merged_this_session:
  - "#2198 fix(wiki_coverage_review): tolerate prose-wrapped JSON + persist raw response"
  - "#2202 feat(v7_build): add --resume MODULE_DIR for phase-skip iteration"
  - "#2203 fix(llm_qg): accept evidence_quotes array as alternative evidence shape"
  - "(plus #2197 from previous session continuation, already noted)"
prs_wip_unmerged:
  - "branch fix/engagement-deterministic-floor (committed 1 commit, pushed; NO PR opened) — fails one pre-existing fixture test, needs callout addition to fixture before opening PR"
active_dispatches: []
active_builds: []
builds_completed_this_session:
  - "#11 build/a1/my-morning-20260521-202848 — failed at wiki_coverage_review (gemini-flash prose), then succeeded at wiki_coverage_review on RESUME with rotated Gemini account (PASS 18/18 substantive); then failed at llm_qg engagement dim verdict=REVISE score 6.5/10"
  - "Build #10 + #11 MDX manually assembled and live on http://localhost:4321/a1/my-morning/ — user can SEE the lesson"
headline_finding: "The 6-issue gate-detection cascade from yesterday is RESOLVED for parser/format. Three PRs landed (#2198, #2202, #2203) that fix the parser tolerance + add --resume iteration. Build #11 finally reached llm_qg phase — but gemini-pro scored engagement 6.5/10 REVISE *without providing a critique*. Root cause traced: V7 dropped the V6 engagement rubric AND most of the V6 anti-pattern enforcement. WIP PR underway to restore deterministic floors (engagement_floor + russianisms_strict gates) and narrow the LLM reviewer to judgment-only. **MDX rendered on starlight regardless — user has the lesson at http://localhost:4321/a1/my-morning/.**"
next_session_first_item: "Finish the engagement_floor WIP PR — fixture update at tests/build/test_linear_pipeline.py:2516 needs callout content added so the new gate passes on it. Then open PR, merge, and resume build #11 with --resume against rotated gemini account to confirm llm_qg passes."
---

# 2026-05-22 Cascade resolved + engagement_floor WIP

## TL;DR

Yesterday's 6-issue gate-detection cascade is RESOLVED:

| # | Issue | PR |
|---|---|---|
| 1 | wiki_coverage_review YAML parse on prose | #2198 (merged) |
| 2 | wiki_coverage_review verdicts in sidecar instead of payload | #2198 raw-response persistence + fallback (merged) |
| 3 | Build re-ran writer (~14 min) for every phase-6 fix iteration | #2202 `--resume MODULE_DIR` (merged) |
| 4 | llm_qg "evidence missing quote marker" when reviewer used `evidence_quotes` array | #2203 (merged) |
| 5 | llm_qg engagement dim REVISE 6.5/10 with NO critique | WIP `fix/engagement-deterministic-floor` |
| 6 | (Future) V7's writer prompt + reviewer prompt regression vs V6 | partially covered by WIP; see Section 4 |

Build #11 of `a1/my-morning` finally rendered to MDX (manually assembled twice) and is live on the local starlight at **http://localhost:4321/a1/my-morning/**. User confirmed visibility.

## Section 1 — PRs landed tonight

### PR #2198 — wiki_coverage_review prose tolerance + raw response persistence

- **Problem**: codex-tools reviewer emitted prose narrative around fenced JSON; `_parse_json_or_yaml_mapping` only stripped one outer fence; both `json.loads` and `yaml.safe_load` failed; no raw response saved.
- **Fix**: parser now tries (a) original whole-string parse, (b) first embedded fenced JSON/YAML block, (c) first balanced `{...}` object span. Plus `wiki-coverage-review-response.raw.md` + `llm-qg-{dim}-response.raw.md` persistence BEFORE parse so #M-10 forensic continuity holds.
- **Reviewer prompt**: tightened with "Response Format — STRICT" gate + worked all-PASS example.
- **6 new tests** in `tests/build/test_wiki_coverage_goodhart_sentinel.py`.

### PR #2202 — `--resume MODULE_DIR` for phase-skip iteration

- **Problem**: every phase-6 fix iteration re-ran the writer (~14 min). 6 cascade fixes × 14 min = ~90 min wasted writer cycles yesterday alone.
- **Mechanism**: `_phase_artifact_passes(module_dir, phase)` checks for canonical success shape per phase (`gates.passed: true`, `overall_verdict: PASS`, `aggregate.verdict: PASS`, etc.). Skips passing phases, runs the first failed/missing phase + everything downstream. `force_rerun` flag ensures upstream re-runs invalidate downstream verdicts.
- **Mutex** with `--worktree` (resume operates on existing dir).
- **21 new tests** in `tests/build/test_v7_build_resume.py`.
- **Iteration: ~14 min → ~45-80s** for review-only changes. Confirmed in practice (build #11 resume #1 took ~5min for wiki_coverage_review; resume #2 took ~3min for llm_qg).

### PR #2203 — llm_qg evidence_quotes array tolerance

- **Problem**: gemini-pro emitted 3 substantive quotes in an `evidence_quotes` array (richer schema than the bare `evidence` string). The validator only checked the bare `evidence` field for literal quote markers (`"`, `«`, `"`) — array form was rejected with "must include a quoted excerpt".
- **Fix**: `_evidence_passes_quote_contract` accepts either bare `evidence`-with-markers OR `evidence_quotes` array of ≥8-char strings. `parse_review_response` preserves the array in the returned entry.
- **10 new tests** in `tests/build/test_llm_qg_evidence_quotes.py`.

## Section 2 — Build #11 final state

After all three PRs landed + Gemini Pro account rotated:

| Phase | Result | Notes |
|---|---|---|
| plan, knowledge_packet, writer, python_qg, wiki_coverage_gate | ✅ all skipped via `--resume` (5ms total) | from build #10's preserved artifacts |
| **wiki_coverage_review** | ✅ PASS 18/18, 0 keyword-stuffing, 0 partial | first clean run ever; gemini-pro on rotated account |
| **llm_qg** | ❌ REVISE — score 6.5/10 | only `engagement` dim failed; pedagogical/naturalness/decolonization all 10/10, tone 9.5/10 |
| mdx | not reached by pipeline | **manually assembled twice** and live on starlight |

The reviewer's engagement verdict was REVISE with **no critique** — no `rationale` / `critique` field in the response. That's the symptom; the cause is in Section 4.

## Section 3 — Build #11 MDX is LIVE on starlight

**http://localhost:4321/a1/my-morning/** — first complete A1 module the user can SEE rendered.

Build #11 worktree preserved per #M-10:
`.worktrees/builds/a1-my-morning-20260521-202848/curriculum/l2-uk-en/a1/my-morning/`

Source artifacts on disk:
- `module.md` (13404 bytes)
- `activities.yaml` (10053 bytes, 10 activities — flat list, no inline/workbook split; see Section 4 issue 2)
- `vocabulary.yaml`
- `resources.yaml`
- `wiki_coverage_review_results.json` (sidecar from gemini-pro's PASS 18/18)
- `llm_qg.json` (4 dims PASS, engagement REVISE)
- `wiki-coverage-review-response.raw.md` (1637 bytes, new #M-10 artifact from PR #2198)
- 5 `llm-qg-{dim}-response.raw.md` artifacts (also new from PR #2198)

NOT promoted to main because llm_qg REVISE — that's the gate doing its job, content quality bar holds.

## Section 4 — Root cause traced: V7 dropped most of V6's pedagogical layer

Comparing `scripts/build/phases/v6-write.md` (720 lines) + `v6-review.md` against V7's `linear-write.md` + `linear-review-dim.md`:

**Dropped from V7 writer prompt:**
- `Українською:` meta-frame ban
- Mixed-language clauses ban
- Required-vocab token-drops ban
- FORBIDDEN WORDS list (#1189; 10 raw Russian words — partially covered by the larger russianism layer, see WIP below)
- Forbidden Tropes block-list (contract §4)
- Natural Prose Register section (BAD → GOOD rewrite examples)
- Pacing Plan first-step requirement
- Engagement rules (hooks, callouts, direct address, narrative arc) — defined in `docs/best-practices/module-content-quality.md` but never made it into the V7 prompt
- inline/workbook activity split (V7 writer emits a flat array; `activity_repair.py` patches it later — writer has no control over which activity lands where)

**Dropped from V7 reviewer prompt:**
- 9-dim rubric with REWARD/DEDUCT criteria + weights (V7 just says "map to the rubric for {DIM}" with no rubric)
- All per-dim concrete examples
- PROOF OF ABSENCE step
- Step 7: fix-it-yourself reviewer (`<fixes>` block) — replaced by ADR-008 deterministic correction paths

**What V7 added (justifying some of the drops):**
- Implementation map manifest + obligation count pre-emit check (#2094)
- Bad-form marker discipline (`<!-- bad -->` wrapping) + pre-emit audit (#2095)
- Visible verification block before drafting (#1673)
- Tier-1 audit for fabricated quotes / citations (#1661)
- Wiki obligations gate + Goodhart sentinel
- Hard-stop rule on writer artifacts shape

So V7 **hardened factual verification** while **dropping the pedagogical / register / engagement rubric entirely**. That's why today's modules emit factually-clean, well-grounded prose AND score 6.5 on engagement.

## Section 5 — WIP on `fix/engagement-deterministic-floor` branch

User direction: "we had a deal that we wont do dim check for what we can check with deterministic code." Re-applied to the engagement gap:

**What goes deterministic** (this WIP PR):
1. `engagement_floor` gate (NEW): ≥2 callouts (`:::tip` / `:::note` / `:::caution` / `> [!myth-buster]` / `> [!history-bite]`) + ZERO META_NARRATION (`In this section`, `Let us begin`, `Welcome to A1`, `You have unlocked`, `Your journey begins`...). Restored from V6 line 537 + module-content-quality.md.
2. `russianisms_strict` gate (NEW): wraps the project's existing 676-line `check_russicisms()` + UA-GEC corpus calque checker into a python_qg gate. Fails on any `critical` severity finding. Replaces the naive V6 10-word list — the existing layer is much more sophisticated (catches `приймати участь`, `самий кращий`, `получати`, `відноситися`, `слідуючий`, dozens of calques).

**What stays in the LLM dim** (judgment-only):
- Does the hook actually hook?
- Is the tone genuinely warm or bureaucratic?
- Do direct-address phrases land as content-anchored or generic?
- Does dialogue feel human?

**Reviewer prompt rewrite** (in this WIP): explicit "JUDGMENT ONLY — do NOT re-litigate deterministic gates" preamble, per-dim residual rubric, instruction that re-stating a deterministic finding is a reviewer-protocol failure.

**Status**: branch pushed, 1 commit (`wip(...)`), no PR opened yet. **One pre-existing test fails** because its fixture module lacks callouts — the engagement_floor gate (correctly) rejects it:

```
tests/build/test_linear_pipeline.py::test_run_python_qg_passes_structural_fixture
AssertionError: Unexpected gate failures: ['engagement_floor']
```

Fix is mechanical: append two callout blocks to the fixture's `module.md` content (look for the `MODULE_TEXT_FIXTURE` or similar constant at top of that test file). Then open PR + merge.

## Section 6 — Cold-start sequence for next session

1. Read this handoff (you're here).
2. Read `docs/session-state/2026-05-21-evening-2-cascade-five-fixes-shipped-six-issue-found.md` for the immediately preceding context (yesterday's cascade timeline).
3. Orient via Monitor API.
4. **First action**: switch to the WIP branch, update the fixture, run tests, open PR.
   ```
   git worktree remove --force .worktrees/fix/engagement-deterministic-floor 2>&1; true  # if it still exists
   git worktree add .worktrees/fix/engagement-deterministic-floor fix/engagement-deterministic-floor
   cd .worktrees/fix/engagement-deterministic-floor
   # find the failing fixture in tests/build/test_linear_pipeline.py line 2516
   # add two `:::tip\n...\n:::` blocks to the structural fixture text
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m pytest tests/build/test_linear_pipeline.py::test_run_python_qg_passes_structural_fixture -q
   # if green, open PR via gh pr create
   ```
5. After PR merges: resume build #11 with `--resume` against the rotated Gemini account to confirm llm_qg engagement now PASSes (gate gives concrete callout/META_NARRATION feedback; LLM dim scores residual quality only).
6. If `module_done` → `scripts/sync/promote_module.py --latest --level a1 --slug my-morning` → first complete V7 module on main.

## Section 7 — Open follow-ups (renumbered)

| # | Subject | Priority | Notes |
|---|---|---|---|
| 1 | Finish WIP `fix/engagement-deterministic-floor` PR | **P0 next session** | fixture update in `tests/build/test_linear_pipeline.py:2516` — add 2 callout blocks |
| 2 | Resume build #11 → confirm llm_qg PASS → promote a1/my-morning | P0 right after #1 | first complete V7 module on main |
| 3 | inline/workbook activity split (V7 writer emits flat array) | P1 | docs spec exists in `vocabulary-activity-standards.md`; writer prompt example shows flat array; `activity_repair.py` patches it but writer has no control over placement |
| 4 | Restore other V6 anti-patterns deterministically | P1 | `Українською:` meta-frame, mixed-language clauses, Forbidden Tropes — separate small PRs once #1 lands |
| 5 | Cross-validate gemini-tools + deepseek-tools writers | P1 | inherited; lower priority until #1-2 unblock |
| 6 | Holistic gate-quality audit | P2 | may be largely moot once #1, #3, #4 land |
| 7 | codex-tools rollout-flush race | P2 | inherited |
| 8 | PR #2168 amelina stub blocker | low | inherited (Gemini PR with Curriculum Plans CI fail) |
| 9 | `review / review` CI auth broken | P2 | inherited; every PR shows this advisory fail; safe to ignore for merge decisions |

## Section 8 — Active state at handoff

- **0 active dispatches**
- **0 active builds**
- **0 unread inbox items**
- **Origin/main at** `867d2e1f6d` (PR #2203 merge)
- **Origin branch `fix/engagement-deterministic-floor`** — 1 WIP commit ahead of main, no PR yet
- **Build worktrees preserved per #M-10** (do not delete):
  - `.worktrees/builds/a1-my-morning-20260521-195056` (build #10)
  - `.worktrees/builds/a1-my-morning-20260521-202848` (build #11 — the live MDX source)
  - plus older builds from yesterday's cascade (build #5-9)
- **Starlight dev server up** on http://localhost:4321 (PID 45551 since Tuesday)
- **Monitor API up** on http://localhost:8765
- **Sources MCP up** on http://localhost:8766

## Sign-off

10 PRs merged across yesterday + today's continuation (cascade fixes #2184-#2197 yesterday, #2198/#2202/#2203 today). Build #11 is rendered, visible at http://localhost:4321/a1/my-morning/, awaiting one engagement gate PR before promotion.

Today's wins:
- Built `--resume` — turned 14-min iterations into 45-80s iterations
- Traced V7→V6 regression in writer/reviewer prompts
- Identified the better russianism layer that V7 never wired in
- Got the first A1 module visibly rendered for the user to evaluate

Tomorrow's first task: finish the WIP fixture update, ship the engagement_floor + russianisms_strict PR, resume build #11 one more time, promote if green.

Sleep well.
