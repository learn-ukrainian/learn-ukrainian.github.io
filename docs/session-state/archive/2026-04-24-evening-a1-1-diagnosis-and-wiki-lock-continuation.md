# Session Handoff — 2026-04-24 evening: a1/1 diagnosis + wiki-lock continuation kickoff

> **TL;DR** Session opened ~16:55 UTC with handoff chain from 14:40 handoff (Phase A merged). Resolved local-main divergence (2 local commits were duplicates of origin's 8-commit lead; merged via conflict-resolution + reset to origin). Shipped PR #1534 (review concurrency cap default 3). Diagnosed a1/1's post-rebuild `plan_revision_request` terminal — **NOT Phase B's fault; writer-side vocab-YAML coverage is the real blocker**. Got Codex agreement via neutral-brief consult (they disagreed with my first framed consult — real adversarial review this time). Dispatched 5 infrastructure PRs; 2 merged (#1535 governance, #1536 vocab validator); 3 still open. Filed #1537 as the long-missing tracking EPIC for the remaining 106 wiki locks (37 a1 + 69 a2). Dispatched first wiki-lock worker (this-and-that, a1/M12) as batch-1 kickoff.
>
> **Critical context the next session needs:** user is frustrated about (a) me NOT having traces for work ("you cannot have thing done without trace"), (b) rubber-stamping Codex consults instead of doing real adversarial checks, (c) asking which wiki instead of just doing them all. The wiki workstream is top priority — "first a1 then a2 wikis very important" (106 reviews total).

---

## What shipped this session (newest first, origin/main tip: `4309d9ce8b`)

| Commit / PR | Subject |
|---|---|
| (PR #1536 merge SHA TBD) | `feat(validator): vocab-YAML coverage pre-review gate` — unblocks a1/1 convergence class |
| (PR #1535 merge SHA TBD) | `feat(api): /api/state/governance endpoint` (closes #1523) |
| `4309d9ce8b` (#1534) | `fix(review): cap per-dim reviewer concurrency (default 3, was 9)` + drive-by test-fixture fix |
| local merge resolution | Pulled origin/main (8 commits behind): #1521/#1524/#1528/#1530/#1531/#1532/#1533 + 14:40 handoff doc. Resolved 3 conflicts by taking origin (verified superset). Reset via `--mixed` to avoid non-squash merge commit. |

## Issues / PRs state

### Closed
- **#1536** merged — vocab-YAML coverage validator (`--step vocab-check`, lemma-aware comparison via VESUM). Ready to wire into default pipeline in a follow-up PR.
- **#1535** merged — `/api/state/governance` endpoint (closes #1523).
- **#1534** merged earlier in session — review concurrency cap.

### Open
- **#1538** `feat(writer-prompt): vocab-YAML coverage + звук/літера discipline` — CI running as of handoff write. Merge when green. Branch: `claude/writer-prompt-vocab-and-phonetics`. Worktree `.worktrees/dispatch/claude/writer-prompt-vocab-and-phonetics`.
- **#1537** (FILED this session) — **EPIC for remaining 106 wiki locks.** 38 a1 slugs listed as AC-1, 69 a2 slugs as AC-2. Tracks the continuation of #1412. Dispatch protocol + rubric doc + #1416 Keychain mitigation all referenced.

### In flight (DO NOT TOUCH)
- **`.worktrees/dispatch/claude/1529-honesty-reviewer-tighten`** — Claude dispatch, running. Will produce PR tightening `v6-review-honesty.md` to credit writer-emitted VERIFY markers. Task id `1529-honesty-reviewer-tighten`.
- **`.worktrees/dispatch/claude/1526-item1-batch-patchability`** — Claude dispatch, running. Will produce PR resolving #1526 item 1 (batch-patchability semantics). Brief told Claude to pick between Path A (reviewer-prompt contract change) and Path B (rename+docs); default Path B. Task id `1526-item1-batch-patchability`.
- **`.worktrees/dispatch/claude/wiki-lock-this-and-that`** — Claude dispatch, running. First wiki-lock worker for a1/M12. Will produce PR `feat(quality): review-and-lock this-and-that wiki + plan (a1 continuation, batch 1)`. Task id `wiki-lock-this-and-that`. Brief at `/tmp/briefs/wiki-lock-this-and-that.md`.

## Big diagnoses + decisions made

### D1 — Phase A worked; Phase B is NOT the fix for a1/1

Previous session's handoff (14:40) said "if annotator still injects markers, we ship Phase B (semantic claim-audit)." After rebuild with Phase A pipeline, empirical data:
- Writer emitted **6 VERIFY markers** with specific claim content
- Annotator injected **0** (honesty-annotations.json = `[]`)
- Honesty dim climbed **5.0 → 7.0** (+2.0)

Phase B gate ("≥3 additional claims the regex annotator catches beyond writer") **NOT MET** — only 1 clearly-unmarked semantic claim ("register mismatch normal in Ukrainian classrooms"). Shelved until a module shows regex missing ≥3 real claims.

### D2 — Real blocker is writer-side vocab-YAML coverage

Convergence terminal `plan_revision_request` from a PERSISTENT FINDING that's fundamentally non-patchable: "Regenerate the module so every required-vocabulary term from the plan appears in the vocabulary YAML." Attempt-1 patched 2 findings; attempt-2 produced identical content (`content_hash_repeat`) because you can't find/replace your way into a missing YAML entry.

Plan has `vocabulary_hints.required` (14 entries). Manual diff shows writer's словник YAML has all 14 modulo stress marks / inflection — so the reviewer finding may itself be a false positive (no stress-stripped comparison). Either way the fix is the same: **deterministic pre-review validator with lemma-aware comparison** → PR #1536 (merged).

### D3 — #1526 item 2 (anchor-matching parity) deferred

My initial read was "content_hash_repeat → anchor-matching failure → #1526 item 2." Wrong. Codex neutral-brief consult correctly pointed out: the stall is the non-patchability classifier working correctly on an unpatchable finding class, not an anchor-selection failure. Item 2 still waiting for empirical data (≥5% of real reviewer outputs needing strategies 2-4 from apply-step).

### D4 — Advisory consult methodology

First Codex consult this afternoon (msg 438/439, task `1529-phase-b-gate`): I framed the brief to lead the witness ("I want to push back on Phase B and want your independent read"). Codex mirrored my three points. User caught me: "do you have an agreement with gpt?"

Redid as task `1529-phase-b-neutral` (msg 440/441): neutral brief with raw data + open-ended question. Codex disagreed with my initial read in 2 of 3 points, forcing real reconciliation (msg 442/443). Lesson: **framed consults + single-model agreement ≠ adversarial review.** The pattern the user endorsed: neutral brief first → see if we actually converge → escalate to Gemini with both sides if we don't.

### D5 — Wiki-lock protocol trace (user's "you cannot have thing done without trace")

The 17 LOCKED a1 pedagogy wikis were produced Apr 22-23 as scale batches, one PR per slug, Claude Code dispatches following `docs/best-practices/wiki-plan-review-and-lock.md` rubric. Pattern per PR:
1. AC-1: wiki → 9+/10 on 5 dims + emit LOCKED review file
2. AC-2: plan lifecycle markers + plan-review checklist
3. AC-3: cross-agent adversarial review via `ask-codex` (NOT ask-gemini, per #1416 Keychain mitigation)
4. PR left unmerged for user review

Commit pattern: `feat(quality): review-and-lock {slug} wiki + plan (scale batch N) (#PR)`. The continuation never got a tracking EPIC — now fixed as **#1537**.

## Files touched on main this session (beyond merged PRs)

No direct main-checkout edits from me; all code changes went via dispatched PRs. User's working tree (as of session start) still has in-flight a1/1 rebuild artifacts and wiki index edits — **do not touch those**, they're user's own in-progress work.

## Next session priorities (order matters)

### P1 — merge the 3 remaining open PRs as they settle

1. **#1538** writer-prompt rules — should be ready to merge shortly (CI was still running at handoff time). Advisory Gemini-Dispatch `review / review` will fail (same GEMINI_API_KEY missing in runner as #1534/#1535); not blocking.

2. **PR from `1529-honesty-reviewer-tighten` dispatch** — expected to appear as Claude finishes. Check `gh pr list` + `ls .worktrees/dispatch/claude/1529-honesty-reviewer-tighten`.

3. **PR from `1526-item1-batch-patchability` dispatch** — expected to appear. This one has a design decision baked into the brief (Path A vs Path B) — read the PR description carefully; the dispatched Claude was told to justify the choice in the PR body.

4. **PR from `wiki-lock-this-and-that` dispatch** — the first wiki-lock continuation PR. When this lands, read it closely. It's the template that will scale to 105 more. If it's clean (9/10 × 5, AC-3 done via ask-codex, no blocked-review-and-lock escalation needed), comment on #1537 with slug + scores + PR number + merge verdict.

**Cleanup protocol per PR merge:**
```
gh pr merge <N> --squash --delete-branch
git worktree remove .worktrees/dispatch/claude/<task-name>
git branch -d claude/<branch-name>   # if still exists
```

### P2 — after this-and-that PR is clean, scale wiki dispatches

User's explicit priority: "first a1 then a2 wikis very important, we need to do all a1." 37 a1 slugs remaining per #1537.

**Suggested parallelism:** 3-4 Claude wiki workers in flight simultaneously (user's earlier cap was "3 claude + 2 codex" — for wiki work, Codex isn't the right fit, so all-Claude). Brief template: `/tmp/briefs/wiki-lock-this-and-that.md` (adapt per slug — change the closest-topic LOCKED reference, the slug paths, the PR title).

**Next 3 slugs in curriculum order (after this-and-that, a1/M12):**
- many-things (a1/M13) — plural topic. Closest-LOCKED reference: things-have-gender.
- checkpoint-my-world (a1/M14) — checkpoint wiki. Closest-LOCKED reference: checkpoint-first-contact.
- what-i-like (a1/M15) — preferences. Closest-LOCKED reference: what-is-it-like (adjective/predicate).

**Dispatch command template:**
```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent claude --effort xhigh --model claude-opus-4-7 \
  --task-id wiki-lock-<slug> \
  --mode danger \
  --worktree .worktrees/dispatch/claude/wiki-lock-<slug> \
  --prompt-file /tmp/briefs/wiki-lock-<slug>.md \
  --hard-timeout 3600
```

Then update #1537 as each lands.

### P3 — a1/1 re-run with full Phase-A + vocab-validator + writer-prompt-hardening

Once #1538 is merged AND vocab validator is wired into default `_ALL_PHASES` (follow-up to #1536 — **not done yet**; #1536 only exposed `--step vocab-check` manually), user can re-run:

```
.venv/bin/python scripts/build/v6_build.py a1 1 --force \
  --writer claude-tools --reviewer codex-tools
```

Expected outcome: plan_adherence vocab finding caught BEFORE the expensive review cycle. Honesty dim ≥8 (writer prompt + rubric tightening). Factual dim ≥8 (звук/літера discipline rule). All dims ≥8 → MIN-gate PASS → first built A1 module.

Failure modes to watch if it still fails:
1. Validator false negative — словник looks complete to validator but reviewer still flags missing. → Debug validator's lemma comparison.
2. Honesty still <8 — rubric tightening didn't convince reviewer. → Read a few Honesty dim findings; tighten rubric further OR reconsider whether reviewer is being too strict on format.
3. Some NEW failure class. → Diagnose before reaching for Phase B.

### P4 — a2 wikis after a1 completes

**69 a2 grammar wikis**, all under `wiki/grammar/a2/*.md` (NOT `pedagogy/a2/` — I made that mistake earlier this session). All compiled by gemini-2.5-pro on Apr 21; paired sources.yaml present 69/69.

Review-path directory is different: `wiki/.reviews/grammar/a2/{slug}-review-LOCKED.md` (new directory — verify on first one).

Per #1537 AC-2. Same dispatch pattern.

## Open carry-overs (not blocking #1537 wiki marathon)

- **#1526 item 1** (batch-patchability semantics) — in-flight dispatch.
- **#1526 item 2** (anchor-matching parity) — deferred per Codex neutral consult.
- **#1526 item 3** (duplicate/overlapping anchors) — low priority, waiting on empirical evidence.
- **#1451** Alignment-Pipeline Runtime Contracts EPIC.
- **#1435** wiki sources.yaml backfill across 227 files.
- **#1522** postmortem management automation.
- **#1395** `/api/git/cleanup` endpoint.
- Phase B (semantic claim-audit) — shelved; revisit if a module shows regex missing ≥3 real claims.

## Things NOT to do next session

- **Do NOT self-review dispatched-Claude PRs** — but reviewing a FRESH-context Claude dispatch's output is independent cross-pairing, fine.
- **Do NOT touch user's a1/1 pilot working tree** (`curriculum/l2-uk-en/a1/sounds-letters-and-hello*` files are user-active).
- **Do NOT rubber-stamp Codex consults** — use neutral briefs first per D4 above. Escalate to Gemini with both sides if we disagree.
- **Do NOT dispatch to Gemini for adversarial review** (per #1416 Keychain mitigation). Use `ask-codex` for cross-agent review of wiki locks.
- **Do NOT revive Phase B design** without empirical evidence of ≥3 unmarked semantic claims per module.
- **Do NOT use `--step all --resume`** (MEMORY #2 warning — destroyed a2-bridge in prior session).
- **Do NOT touch `.worktrees/codex-interactive`** — user's long-lived sandbox; detached HEAD at `3c8bc39bae`.

## Tool + agent state at handoff

| Agent | Status |
|---|---|
| Codex | Idle. 2 dispatches today completed (#1535 + #1536). |
| Claude (headless dispatches) | **3 in flight** — `1529-honesty-reviewer-tighten`, `1526-item1-batch-patchability`, `wiki-lock-this-and-that`. All at xhigh effort. |
| Claude (me, this session) | Context elevated after 5+ hours. Handing off. |
| Monitor API | Status unknown — was DOWN at session start. Did not verify during session. |

## Context accounting

- Session ran roughly 5.5 hours (16:55 UTC cold-start → ~22:20 UTC handoff write).
- Peak work density middle 2 hours (dispatches, consults, merge resolution).
- Last ~1 hour was wiki-trace investigation + #1537 filing + first wiki dispatch.
- Did NOT use `/compact` or `--resume`. Fresh session + this diary is the pattern per MEMORY #2.
- Next session cold-start: Monitor API bootstrap per `workflow.md` (if API is up), `gh pr list` (see which of the 3 in-flight dispatches landed), `ls -lt docs/session-state/*.md | head -5` (read this file + 14:40 + 10:25 in chain).

## One-line summary for `current.md`

> 2026-04-24 evening: Phase A validated on a1/1 (writer cooperation working, annotator idle); vocab-YAML coverage identified as real convergence blocker → validator merged #1536 + writer-prompt PR #1538 open; wiki-lock continuation kicked off via #1537 + first dispatch (this-and-that); 3 Claude dispatches still running at handoff.

---

*Generated 2026-04-24 ~22:20 UTC. Tip of origin/main: `4309d9ce8b` (this session's concurrency cap). 3 Claude dispatches in flight. User priority: finish a1 wiki locks (37) then a2 (69).*
