# Session Handoff — 2026-05-02 (POC plan locked, prereqs merged)

> **Predecessor:** `2026-04-30-dependabot-lockfile-fixes-and-uk-framing-clarification.md`
> **Successor scope:** Execute the M20-anchor-first POC plan once #1636 merges. Spot-check L1 wikis → run V7 linear_pipeline on M20 with Gemini-tools writer → user-eval checkpoint A → proceed to M1 if pass.
> **Mode:** Active autonomous run during user-away window. Compute budget hot (<10% Anthropic weekly remaining for 2 days as of session start). All execution dispatched to Codex/Gemini; Claude coordinates only.

---

## TL;DR — what locked in this session

1. **Two pipeline prereqs shipped** — #1635 (wiki+MCP retrieval, retires Qdrant; closes #1631 #1625 #1629) merged; #1636 (ADR-008 per-gate correction paths; closes #1632) rebased + CI in flight, merging momentarily.
2. **POC plan reframed and locked in #1577** — replaces #1622 round-4 bakeoff (1 module) with a 4-module anchor-first sequence (M20 → M1, M2, M3) and explicit checkpoints between each phase.
3. **Pedagogy framing made explicit** — zero-onset / immersion-ramp / 100%-immersion threshold are three qualitative inflections, NOT a smooth curve. No "neutral" baseline module in a decolonized curriculum. M20 my-morning chosen as anchor over M10 colors precisely because colors carries Russian-imperial propaganda load (per user 2026-05-02).

---

## Commits to main this session

```
0c42c13665  feat(linear_pipeline): wiki+MCP knowledge packet, retire Qdrant path (#1631) (#1635)
            └─ b1ad3b58e0 (fix-commit on PR branch) deleted scripts/research/build_knowledge_packet.py
                                                    per Gemini REVISE finding 5
            └─ 3aba07df1f (Codex initial commit on PR branch)
```

`#1636 → main` merge pending CI completion. Branch `codex-1632-adr-008-impl` head: `d3d9e3e04e` (rebased onto main post-#1635).

Issues auto-closed by #1635 merge: **#1631, #1625, #1629**. #1632 will close on #1636 merge.

---

## The POC plan (canonical reference: #1577 comment)

Permalink: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1577#issuecomment-4363291518

### POC modules (4 total, sequential)

| Slot | Slug | Sub-track | Purpose |
|---|---|---|---|
| 0 | A1/M20 `my-morning` | A1.3 Actions | **ANCHOR** — Type B steady-state, lower decolonization confound, has prior round-3.5 evidence to compare against. Disambiguates "V7 broken" vs "zero-onset specifically broken." |
| 1 | A1/M1 `sounds-letters-and-hello` | A1.1 Sounds, Letters, First Contact | Type A zero-onset checkpoint — does the writer work on the hardest pedagogical case? |
| 2 | A1/M2 `reading-ukrainian` | A1.1 | Scaffolding — does M2 reuse M1's letter knowledge correctly? |
| 3 | A1/M3 `special-signs` | A1.1 | Scaffolding chain — does writer hold over 3 sequential zero-onset modules? |

All 4 wikis exist on disk (`wiki/pedagogy/a1/{slug}.md` + `.sources.yaml`, 20-31KB each). Verified at session time.

### Sequence (executable when user returns)

1. ✅ Merge #1635 + #1636 (in flight — #1635 done, #1636 CI almost done).
2. **Spot-check L1 wikis** for the 4 POC slugs against Framing-A bar: citations dense, decolonized register, standalone-publishable. ~10 min, cheap. If any wiki fails, regenerate via `compile.py --writer gemini` BEFORE L2 build.
3. **Run V7 linear_pipeline on slot 0 (M20) ALONE** with **Gemini-tools writer**.
4. **Checkpoint A — user evaluates anchor**:
   - Pass → V7 baseline works → proceed to slot 1 (M1).
   - Fail → V7 has a fundamental issue. Diagnose at gate level, fix, retry M20. **Don't waste M1-M3 cycles** — zero-onset will be even harder; fix the easier case first.
5. Run slot 1 (M1).
6. **Checkpoint B — user evaluates zero-onset**:
   - Pass → proceed to slots 2-3.
   - **Fail with anchor passing** → strong signal that V7 needs `module_type` branching. File new issue at this point. **Don't pre-build it.**
7. Run slots 2-3 sequentially (test scaffolding chain).
8. Final checkpoint → if all 4 pass, scale decision (next 5-10 modules → checkpoint → batch).

### Hard rule on scaling (user-stated 2026-05-02)

```
M20 (anchor) → checkpoint A → M1 → checkpoint B → M2-M3 → checkpoint final → next 5-10 → checkpoint → batch
```

NEVER batch all 55 A1 modules after M1-M3 pass. Quality drift creeps in fast at scale. Each checkpoint is a USER-EVAL gate, not an automated one.

### Writer choice (locked: Gemini-tools first)

Single-writer POC. Don't run claude-tools in parallel for A/B until quality is borderline at a checkpoint — that's 2× compute for evidence we don't yet need. Anthropic budget is hot. If Gemini fails or quality borderline → dispatch claude-tools on the same module(s) for direct A/B.

---

## Pedagogy framing locked in (NEW — propagate to all future agents)

### Three qualitative difficulty inflections, NOT a smooth curve

- **Zero-onset (A1.1 M1-M7, especially M1-M3):** can't use target language to explain target language; heavy L1 scaffolding, phonetic ladders, visual anchoring; wrong examples install permanent bad habits. **This zone has been hard for months — see months-of-struggle context.**
- **Immersion ramp (mid A2 → end A2):** *removing* L1 scaffolding; force inference from context.
- **100% immersion threshold (B1/M1):** drop L1 entirely.
- **From B1/M1 onwards:** continuous slope, smoother because target language is self-explanatory.

### No "neutral" baseline module in a decolonized curriculum

User correction 2026-05-02: every module touches some sensitive ground. My initial proposal of A1/M10 colors as "neutral steady-state baseline" was wrong — colors carries Russian-imperial propaganda load (жовто-блакитний framing, black-and-red, "blue is Russian"). M20 my-morning is cleaner anchor for testing pipeline mechanics because everyday-routines content has lower decolonization confound, NOT because it's "neutral."

**Pattern lesson:** when picking a "control" or "baseline" module, the goal is isolating the variable being tested, not finding an "easy" module. There are no easy modules in this curriculum.

### Architectural watch (do NOT pre-build)

If checkpoint B fails (M1 fails while M20 passes), the months-long M1-M3 struggle is structural. Strong signal to add `module_type` as a first-class plan field with branching writer-prompt strategy:

| Module type | Writer strategy |
|---|---|
| `zero_onset` (A1.1 M1-M7) | L1-heavy, phonetic ladder, visual/iconic anchors, ~80% English |
| `steady_state` (A1.2–mid A2) | Mixed L1+L2, build on prior vocab, standard pattern intro |
| `immersion_transition` (late A2) | Progressively shed L1, force contextual inference |
| `full_immersion` (B1+) | 100% Ukrainian, native-style at lower complexity |

**DO NOT pre-build this.** Let the POC data tell us. Build the architectural fix only if M20 passes AND M1 fails — that's the data signal.

---

## Cross-agent broadcast status

**NOT done this session.** The bridge `architecture` channel thread `be8c4617` (Framing A/B from 2026-04-29) does not yet have the new "no neutral baseline" + "three inflections" framing. Future Claude session OR a small bridge post would propagate to Codex + Gemini so they don't quietly re-import "neutral baseline" reasoning from training-data priors. Defer to user request.

---

## Open / pending state

### #1636 in CI

Watcher running (background bash `brz9fixc6`). When CI green:
1. `gh pr merge 1636 --squash --delete-branch` (per memory rule #0H, no need to ask — review done)
2. Verify #1632 auto-closes
3. Clean up worktrees: `.worktrees/codex-1631-wiki-migration` and `.worktrees/codex-1632-adr-008-impl` (both branches still exist locally — `git worktree remove` + `git branch -d`)

### #1622 status

Open. Commented with supersedance pointer to #1577. Not closing — keeping as reference for the original bakeoff goal in case user wants to compare claude-tools later.

### Two minor follow-ups from Gemini PR reviews (not blockers, file as separate issues if user prioritizes)

From #1636 (ADR-008) Gemini APPROVE-with-findings:
1. **Soft enforcement gap (linear_pipeline.py:819):** when pipeline candidate generation yields nothing, the prompt omits the "do not invent" instruction — slightly weakens the ADR-008 invariant. Easy fix.
2. **Reviewer fix-validation gap (linear_pipeline.py:1082):** reviewer's `<fixes>` are applied without runtime validation that the `replace` string strictly belongs to the proposed `candidates` list. Real ADR-008 invariant gap (currently soft-enforced via prompt, not hard-enforced via validation). File as a follow-up.

Both are small. NOT blocking the POC. File post-merge if user prioritizes.

---

## Compute / budget state

- **Anthropic:** <10% weekly remaining for 2 days as of session start (user-stated). All Claude work this session: orchestration only, no inline writing/coding work delegated.
- **Codex:** dispatched both PR implementations (#1631, #1632), 9.85min + 10.43min runtimes. Still well under cap (max 2 in flight, was 2/2 at peak; now 0).
- **Gemini:** 2 adversarial reviews dispatched (PR #1635, #1636). One APPROVE, one REVISE-then-fix-applied. Subscription unmetered.

This session pattern: Codex execution → Gemini review → Claude coordination + minor in-line fixes only when single-line (e.g., the leftover-file deletion on PR #1635 branch). Good ratio for compute-conserving mode.

---

## What's next when user/Claude returns

**Order of operations:**

1. Verify #1636 merged successfully:
   ```bash
   git fetch origin main
   git log --oneline origin/main | head -3
   gh issue view 1632 --json state --jq .state   # should be CLOSED
   ```

2. Clean up worktrees (deferred from this session):
   ```bash
   git worktree remove .worktrees/codex-1631-wiki-migration
   git worktree remove .worktrees/codex-1632-adr-008-impl
   git branch -D codex-1631-wiki-migration codex-1632-adr-008-impl  # safe — already merged
   ```

3. **Spot-check L1 wikis** for the 4 POC slugs (10 min). Read each `wiki/pedagogy/a1/{slug}.md` + `.sources.yaml` against Framing-A bar.

4. **Run V7 linear_pipeline on M20 alone with Gemini-tools writer.** Exact CLI to be confirmed (the V7 entry point was added during the reboot and is referenced in #1635 — check `scripts/build/linear_pipeline.py --help` or trace from a recent test invocation).

5. **User-eval checkpoint A** on M20 output.

6. Branch on outcome per the POC plan.

**If user is checking back in mid-day:**
   - PR #1636 merge status (should be DONE by now)
   - Whether the spot-check L1 wikis pass Framing-A bar
   - Decision to run M20 alone or wait for explicit go-ahead

---

## Cold-start protocol for next session

```bash
# 1. Verify clean state
git status -s              # should be empty
git worktree list          # main only (after step 2 above)
git log --oneline -5       # top should include both #1635 and #1636 merges

# 2. Read this handoff. Then read #1577 comment 4363291518 for the canonical POC plan.

# 3. Verify pending issues
gh issue view 1632 --json state --jq .state  # CLOSED
gh issue view 1622  # superseded, still open as reference
gh issue view 1577  # active EPIC

# 4. Default action: execute step 3 above (spot-check L1 wikis). No user signal needed for spot-check; needs user signal for L2 build.
```

---

## Mid-session update — #1637 V7 CLI gap discovered + Codex dispatched

After #1636 merge: discovered `linear_pipeline.py` has NO `__main__` — it's a pure library, no CLI wrapper. Phase 4 round-3 / round-3.5 used ad-hoc invocations that weren't committed. **POC step 3 ("run V7 on M20") is blocked until a CLI wrapper exists.**

- Filed **#1637** with full spec mirroring v6_build.py's CLI surface.
- Dispatched Codex (`task_id: codex-1637-v7-cli`, gpt-5.5 high, 90-min hard timeout) at session-end.
- Brief: `/tmp/brief-1637-v7-cli.md` — ephemeral, but the issue body has equivalent specification.
- Expected artifact: `scripts/build/v7_build.py` + `tests/build/test_v7_build_e2e.py` + new PR.

### Autonomous actions Claude will take while user is away

1. Monitor `batch_state/tasks/codex-1637-v7-cli.json` for state transition out of `running`.
2. On completion: read final state, find new PR, fetch CI status.
3. Dispatch Gemini for adversarial review (subscription, no Anthropic budget).
4. If CI green + Gemini APPROVE: `gh pr merge {N} --squash --delete-branch` per memory rule #0H.
5. If REVISE/REJECT or CI failure: file findings on the PR, idle for user.
6. After merge: clean up worktree, comment on #1637 closure.
7. **STOP** — POC step 3 (running V7 on M20) requires user-eval, not autonomous execution.

If user returns and #1637 is merged, the executable next step is:
```bash
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer gemini
```
Output goes to `curriculum/l2-uk-en/a1/my-morning/`. User then evaluates checkpoint A.

## Final state

- **2 PRs merged this session** ✅ #1635 (closes #1631 #1625 #1629) + #1636 (closes #1632)
- **4 issues auto-closed** ✅ #1631, #1625, #1629, #1632
- **1 NEW issue filed + dispatched** ✅ #1637 (V7 CLI wrapper) — Codex working on it autonomously
- **#1577 EPIC comment posted + edited** with the canonical M20-anchor-first POC plan
- **#1622 commented** with supersedance pointer (kept open as bakeoff-goal reference)
- **HEAD = `81742658a0`** at write time (or whatever advances when #1637 merges autonomously)
- **0 dirty files** in main checkout
- **0 worktrees** mounted in main (cleaned up post-merge); 1 mounted under `.worktrees/codex-1637-v7-cli` (auto-cleanup on PR merge)
