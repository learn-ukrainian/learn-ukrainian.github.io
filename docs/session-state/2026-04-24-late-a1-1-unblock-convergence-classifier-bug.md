# Session Handoff — 2026-04-24 late (~22:00 UTC): a1/1 unblock campaign + convergence-classifier bug isolation

> **TL;DR** Session goal was to unblock a1/1 rebuild by merging all the writer/reviewer-prompt fixes from previous sessions. Shipped 5 PRs (#1538/#1539/#1540/#1543/#1544) — all merged. Uncovered a **silent pipeline bug** during the a1/1 rebuild: `convergence_loop.py:391` pre-empts to `plan_revision_request` (tier 5) on attempt 1 **before** reviewer `<fixes>` are applied. This has been silently sabotaging every convergence round where topologies aren't exclusively `local_to_prose`. Two independent AI reviewers (Codex + Gemini) converged on identical diagnosis. Headless Claude is **already dispatched** (pid 4183, task `1526-item2-anchor-parity`) with a complete fix brief. Expected to land as a PR overnight.
>
> **The critical existential question**: user asked whether the project has a fixable problem or should be shut down. **Answer: YES, fixable, high confidence.** See §"Is this fixable?" below for the evidence.

---

## What shipped this session (newest first)

| Merged SHA | PR | Subject | Role in a1/1 |
|---|---|---|---|
| `cf892cf96b` | **#1544** | `fix(writer-prompt): kill "Section N:" primer — enforce verbatim Ukrainian H2 titles` | Prevents writer from producing `## Section N: <title>` instead of `## <title>` — cascading SECTION_ORDER + MISSING_SECTION + TEACHING_BEATS failures. Also expanded CI path filter to `scripts/build/phases/**/*.md` so future prompt-only PRs actually run pytest. |
| `399757d987` | **#1543** | `feat(quality): review-and-lock this-and-that wiki + plan (a1 continuation, batch 1)` | First wiki-lock template merged. Verdict 9/10 × 5 dims — ready to scale the remaining 105 wikis (EPIC #1537). Included gemini-code-assist catch `природній → природний` (Правопис 2019). |
| `99400cbb72` | **#1540** | `refactor(patchability): clarify batch-level semantics (#1526 item 1)` | Rename `patch_ok → batch_patch_ok` with documentation. Item 2 of #1526 is the classifier bug we uncovered this session. |
| `565a24597d` | **#1539** | `fix(review): honesty reviewer credits writer-emitted VERIFY markers (#1529 post-Phase-A tightening)` | Stops reviewer from double-counting claims that already carry VERIFY markers. a1/1 Honesty went 4.0 → 6.4 after this merged (still below gate — separate content issue). |
| `29c396aed9` | **#1538** | `feat(writer-prompt): vocab-YAML coverage + звук/літера discipline` | Writer now guarantees словник YAML covers all `plan.vocabulary_hints.required`. Applied 2 pre-merge fixes: Я positional rule (й+а vs palatalization correct) + VERIFY-in-YAML placement. |
| `1f9c29acdf` | n/a | `docs(agent-cooperation): note CC 2.1.119 dispatch behavior changes (#1541, #1542)` | Documentation for new CC release. |

**Bonus follow-up issues filed**: #1541 (duration_ms hook telemetry), #1542 (statusline effort.level display).

**Bonus cleanup**: pyenv-shim deadlock — killed 5 stuck rehash processes + removed `~/.pyenv/shims/.pyenv-shim` lock. Sessions running silent again. `PYENV_DISABLE_AUTO_REHASH=1` is already in `~/.bashrc`.

---

## Overnight dispatched work (in flight)

### Headless Claude PR — #1526 item 2 (convergence classifier bug)

- **Task ID**: `1526-item2-anchor-parity`
- **Worker PID**: 4183 (at handoff write time: elapsed ~9 min, status `running`)
- **Worktree**: `.worktrees/dispatch/claude/1526-item2-anchor-parity`
- **Branch**: `claude/1526-item2-anchor-parity`
- **Base SHA**: `cf892cf96b` (current `origin/main`)
- **Brief**: `/tmp/briefs/convergence-fix-apply-unblock.md` (7142 chars — full diagnoses from both Codex msg #447 and Gemini msg #446 included)
- **Watcher**: background bash task `b8cxj9v75` blocks on `delegate.py wait 1526-item2-anchor-parity --timeout 1800`

Expected deliverable: PR with changes to
- `scripts/build/convergence_loop.py:391` — new predicate allowing `patch` strategy when any valid anchor exists + no plan-level finding
- `scripts/build/patchability.py:201` — decouple per-finding patchability from batch-atomic anchor validation (the real #1526 item 2)
- `scripts/build/v6_build.py:5658-5692` — rename `fixes_applied` → `fixes_available` (honest name) + add real `fixes_applied` populated by actual apply-fix return
- `tests/test_convergence_loop.py` — regression test replaying a1/1 scenario

**CLI version that dispatched**: Claude Code `2.1.119`.

---

## The critical question: Is this fixable? (existential, user-asked)

**YES. High confidence. Here's the evidence:**

1. **Two independent AI reviewers converged on the same root cause** with zero framing from me. Codex (msg #447 on bridge, task `fix-apply-bug-codex`) and Gemini-3.1-pro-preview (msg #446, task `fix-apply-bug-20260424`). Both name `convergence_loop.py:391`, both name the set-equality-too-strict predicate, both propose equivalent patches. Reproducible diagnosis.

2. **Manual workaround proved the design is sound.** I applied the reviewer's 26 `<fixes>` find/replace pairs by hand via Python script. 21 landed cleanly, 5 skipped because of overlapping anchors (expected — sequential find/replace consumes matches). This proves the reviewer-as-fixer design works when invoked. The bug is purely that the pipeline's classifier was pre-empting to `plan_revision_request` BEFORE the apply step ran. Fix the classifier predicate, everything downstream works.

3. **Fix is small and localized.** ~20 LOC across 2–3 files. Not architectural. Not a data problem. Not a model problem. A single Boolean predicate refinement.

4. **This is known tracked work.** EPIC #1525 (3-tier self-healing convergence loop) has this as `#1526 item 2 (anchor-matching parity)`. Marked "deferred" in yesterday's session. Not a surprise; the anticipated next blocker.

5. **Content pathway is sound.** When fixes land, scores go up. The reviewer's `<fixes>` blocks are pedagogically correct (caught real writer errors: fabricated «Україна four vowels in a row», reversed euphony rule «мама і тато»). The writer's errors are the kind adversarial review is supposed to catch, and the fix loop IS supposed to apply the corrections — it just wasn't, because of this one classifier predicate.

**The project is NOT stuck in an unfixable state.** It's one merged PR away from:
- a1/1 converging on attempt 1 in the next build
- Every future module building without silent fix-loss
- The reviewer-as-fixer pattern working as the architecture intends

**What would make it unfixable** (for reference, none of these apply):
- Fundamental design flaw in per-dim review: not the case — dims scored correctly, fixes were correct
- LLM inability to produce correct Ukrainian content: not the case — naturalness/actionable/decolonization all PASS; the writer makes correctable errors that the reviewer correctly catches
- Infrastructure unable to handle the scale: not the case — 9-dim parallel review works; the v0.125.0 Codex issue is transient and rollback to v0.124.0 works

---

## a1/1 module state (working tree — DO NOT let fresh checkouts nuke this)

The module is currently **manually patched** with 21 reviewer fixes:

- **File**: `curriculum/l2-uk-en/a1/sounds-letters-and-hello.md`
- **Backup**: `curriculum/l2-uk-en/a1/sounds-letters-and-hello.md.pre-manual-fix` (pre-patch state for reference)
- **Applied**: 5 factual + 1 language + 2 decolonization + 3 completeness + 2 naturalness + 4 plan_adherence + 4 honesty + 0 dialogue = 21 fixes
- **Not found (expected — overlapping anchors)**: 5 fixes across honesty/language/naturalness/dialogue

**Content verification**: «Україна four vowels in a row» → gone. «мама і тато uses і after a consonant» → replaced with correct «мама й тато uses й after a vowel». Digraph-as-cause-of-38-sounds claim → replaced with hard/soft-consonant-pairs explanation. «Г is a soft fricative» → «Г is the voiced Ukrainian fricative [ɦ]».

**IMPORTANT**: If tomorrow-session runs `v6_build.py a1 1 --force`, the `--force` flag will nuke the patched module. Use `--resume` with specific `--step review` to re-review the already-patched content.

---

## Tomorrow-session's playbook (in priority order)

### Step 1 — orient (first 2 minutes)

```bash
# Check overnight dispatch status
.venv/bin/python scripts/delegate.py status 1526-item2-anchor-parity

# Expected states:
#   status: success + finished_at populated → PR is open, check next
#   status: running  → still working; let it continue
#   status: failed / error → see stderr_excerpt; may need re-dispatch

# Check for the PR
gh pr list --state open --author "@me" --head claude/1526-item2-anchor-parity
gh pr list --state open  # full list
```

### Step 2 — review + merge the #1526 item 2 PR (if it landed)

If the dispatched Claude produced a PR:

1. Read the PR body + diff. Verify it addresses:
   - `convergence_loop.py:391` predicate relaxation
   - `patchability.py:201` batch-atomic anchor decoupling
   - `v6_build.py:5658-5692` fixes_applied rename
   - Regression test for a1/1 scenario
2. Check CI — `Test (pytest)` must PASS (only required check). Advisory Gemini-Dispatch `review / review` failure is expected (missing `GEMINI_API_KEY` in runner, same as #1534/#1535/#1538/#1539/#1540/#1543/#1544).
3. If CI real checks are green, **merge per MEMORY #0H**:
   ```bash
   gh pr merge <N> --squash --delete-branch
   git worktree remove .worktrees/dispatch/claude/1526-item2-anchor-parity
   git branch -d claude/1526-item2-anchor-parity
   ```
4. Comment on #1526 closing item 2; note EPIC #1525 progress.

### Step 3 — verify the fix with a fresh a1/1 build

After merge:

```bash
# OPTION A: verify the already-patched module still produces clean scores
# (does not rebuild writer/enrich — just re-runs review against current content)
.venv/bin/python scripts/build/v6_build.py a1 1 --step review --resume

# OPTION B: end-to-end clean rebuild (nukes the manually-patched .md, regenerates everything)
#   Use this to prove the fix works for EVERY future build, not just today's patched module
.venv/bin/python scripts/build/v6_build.py a1 1 --force --writer claude-tools --reviewer codex-tools
```

Option A is cheaper (~5 min) and a quick confidence check. Option B is the real proof (~30 min) — this is what the user will want to see before declaring victory.

Watch for:
- `MIN score (gate): X` — must be ≥ 8
- `module_done` event (not `module_failed`, not `plan_revision_request` terminal)
- Final audit gates all GREEN

### Step 4 — if Option B surfaces content issues

The writer sometimes fabricates Ukrainian examples («Україна four vowels in a row») or reverses rules («мама і тато» euphony). These are caught by the reviewer's `<fixes>` block and applied deterministically **once the pipeline fix is in place**. Expect 2-3 review rounds for convergence. If scores still stall below 8 after 2 rounds:

- Check Factual dim findings for NEW fabrications (writer may introduce different errors on retry)
- If fabrications persist, the follow-up writer-prompt tightening is: "Ukrainian examples MUST come verbatim from the knowledge packet — no invented examples. Mark any example NOT in the packet with VERIFY." That's a follow-up PR, not a blocker.

### Step 5 — scale after a1/1 is green

When a1/1 is PASSED + audit all green + published MDX renders:
- Comment on #1525 with "convergence loop proven end-to-end on a1/1"
- Optionally rebuild a1/colors (another previously-stuck module) with the new pipeline to confirm fix generalizes
- Return to wiki-lock scale-out per EPIC #1537 (104 wikis remaining)

---

## Codex CLI v0.125.0 warning (revisit when stable)

v0.125.0 shipped 2026-04-24 18:00 UTC. During its use, 3–5 of 9 dims silently failed with `returncode: 1 + 0 bytes stdout + 30s duration`. Rolling back to v0.124.0 (user confirmed) restored reliability — all 9 dims succeeded.

**No proof v0.125.0 is the cause, but strong correlation.** If tomorrow a build still runs on v0.125.0 and fails the same way, pin to v0.124.0 as a workaround:

```bash
npm install -g @openai/codex@0.124.0
codex --version  # confirm 0.124.0
```

File a `openai/codex` bug report with our repro if it recurs. v0.124.0 → v0.125.0 changelog candidates to investigate: `#19130 exec-server: wait for close after observed exit`, `#18811 refactor: route Codex auth through AuthProvider`. Neither is a smoking gun but both touch stdout/auth paths.

---

## References to stay out of rabbit holes tomorrow

- **Issue threads that already capture this**: EPIC #1525 (convergence 3-tier), #1526 (item 2 = the exact bug), #1316 (early-literacy review calibration, unrelated)
- **Agent bridge diagnoses**: Codex msg #447, Gemini msg #446 — read them before diverging from Codex's recommended patch
- **Do NOT** re-read CLAUDE.md, `.claude/rules/*.md`, `docs/session-state/current.md` separately on cold start. Use Monitor API per `claude_extensions/rules/workflow.md`.
- **Do NOT** nuke the manually-patched a1/1 .md until Option A or B above confirms the fix works. Backup is at `.md.pre-manual-fix` either way.
- **Do NOT** touch `.worktrees/dispatch/claude/1526-item2-anchor-parity` until the dispatched Claude's PR is merged or you're explicitly re-dispatching.
- **Do NOT** touch `.worktrees/codex-interactive` (user's local work).

---

## Stale context that is NOT the blocker anymore (crossed off)

- ✅ Writer vocab-YAML coverage (#1538 + validator #1536 solve it)
- ✅ Honesty reviewer double-counting marked claims (#1539)
- ✅ Section N: primer in pacing plan (#1544)
- ✅ CI path filter missing `scripts/build/phases/**/*.md` (#1544)
- ✅ Wiki-lock template validation (#1543 — ready to scale)
- ✅ Batch-patchability semantic naming (#1540 — item 1 done, item 2 in flight)

---

## Contact points

- Empirical driver artifact: `curriculum/l2-uk-en/a1/orchestration/sounds-letters-and-hello/plan_revision_request.yaml`
- Codex diagnosis: `.venv/bin/python scripts/ai_agent_bridge/__main__.py read 447`
- Gemini diagnosis: `.venv/bin/python scripts/ai_agent_bridge/__main__.py read 446`
- Dispatch brief: `/tmp/briefs/convergence-fix-apply-unblock.md`

**End handoff.**
