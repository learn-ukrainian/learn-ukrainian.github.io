# Session Handoff — 2026-05-05 Overnight (claude CLI dispatch fix + CodeQL cleanup orchestration)

> **Predecessor:** `2026-05-05-deliberation-architecture-validated.md`
> **Successor scope:** Pick up from 2 in-flight PRs (#1686 + #1692) awaiting Codex re-review and merge, plus 4 dispatched Gemini draft PRs (#1687/#1688/#1689/#1690) awaiting user security-review on CodeQL fixes.
> **Mode:** User asleep, full autonomous orchestration. Worked the handoff queue + a user-added Gemini code-scanning dispatch in parallel.

---

## TL;DR — what shipped this session

Started fresh after handoff. User added an inline instruction during the session to "have gemini finish the rest of the code scanning problems working in worktree and creating prs fo review."

### Merged this session

- **PR #1693 → main** (commit `4185c0a33c`): `fix(test): align test_discuss_replies_create_delivered with round-1 short-circuit block`
  - Pre-existing main breakage uncovered while landing #1686. The deliberation-protocol fix `872d8791` from 2026-05-05 added round-1 short-circuit block; this test was not updated to use `--max-rounds 2`.
  - Originally bundled into #1686 as the piggyback that unblocked the worktree pre-commit hook. Codex's third blocker on #1686 flagged the bundling as an AGENTS.md:22 + 121-130 violation (one PR = one concern). Split out into #1693 per Codex's recommendation.
  - 24/25 CI checks pass; 1 advisory `review/review` (Gemini-Dispatch) failure is non-blocking per memory rule #0H.

### In-flight / merge-ready at handoff time

- **PR #1686** — `fix(agent-runtime): default Claude adapter to npx@latest, not stale local binary`
  - Branch tip: `25cc04af89` (force-pushed after rebase onto new main with #1693 dropped).
  - State: 2 files only (`scripts/agent_runtime/adapters/claude.py` + `tests/test_agent_runtime.py`); zero `sys.executable` literal anywhere; mergeable per `gh pr view`.
  - Closes #1684 + #1685. **Awaiting fresh post-rebase Codex `[AGREE]`** in thread `ecfc08bf223f` on channel `reviews` (request posted at handoff close). Codex's three previous blockers all addressed:
    1. `sys.executable` runtime fallback violated AGENTS.md:19 → fixed via `git rev-parse --git-common-dir` resolver.
    2. Literal `sys.executable` mention in docstring/error message → reworded to "calling Python interpreter."
    3. Bundled discuss-test fix violated one-PR-one-concern → split out as #1693 (now merged).
  - **Next session: confirm Codex `[AGREE]`, watch CI on `25cc04af89`, merge with `gh pr merge 1686 --squash --delete-branch`, then `git worktree remove .worktrees/claude-1684-prefer-npx`.**

- **PR #1692** — `feat(reviewer): false-positive Russianism guard for v6-review-language`
  - Closes #1691 (filed this session). Implements handoff queue item #5 (audit reviewer prompts for false-positive Russianism handling).
  - Adds two sections to `scripts/build/phases/v6-review/v6-review-language.md`: "Russianism flagging — verify before flagging" + "Known false-positive Russianisms — DO NOT FLAG" (собака, степ, Сибір, біль, посуд).
  - 44/44 contract reference sync tests pass on the worktree.
  - **CI inherited the same pre-existing test failure that #1693 fixed.** After rebasing onto main (post-#1693 merge), the pytest fails should clear. **Next session: rebase onto current main, force-push, re-run CI, send Codex review request, merge if green.** Branch: `claude-1690-reviewer-fp-russianisms`.

### Dispatched, awaiting morning user review
- **PR #1687 [DRAFT]** — Gemini Batch B: 7 CodeQL alerts (stack-trace + clear-text exposure)
- **PR #1688 [DRAFT]** — Gemini Batch D: 8 CodeQL alerts (JS/HTML XSS in playgrounds + podcast HTML)
- **PR #1689 [DRAFT]** — Gemini Batch C: 12 CodeQL warnings (URL substring + bad-tag-filter)
- **PR #1690 [DRAFT]** — Gemini Batch A: 11 CodeQL alerts (py/path-injection)

All 4 are draft for human security review (per dispatch brief — security-class fixes, do NOT auto-merge). Briefs at `docs/dispatch-briefs/2026-05-05-codeql-{A,B,C,D}-*.md`.

### Filed, deferred
- **#1665 (Holovashchuk dictionary ingest)** — Codex dispatch ran 110s, correctly stopped per dispatch's "PDF dead → STOP" condition. The kpdi.edu.ua PDF URL is 404 (verified via curl HEAD, percent-encoded variant, range-byte GET). Comment posted on #1665 with verification details + alternative-source candidates (lounb.org.ua catalog, slovnyk.me linguistic_norm mirror, chtyvo.org.ua). Re-dispatch when an alternative is verified live.

### Filed, surfaced as pending decision
- **`docs/decisions/pending/2026-05-05-adr-008-supersession-question.md`** — answers handoff queue item #2. **My recommendation: keep ADR-008 as-is (option a)**, push back on the handoff's "probably (b)" framing. Argument: ADR-008's per-gate correction loop addresses post-write mechanical failures that deliberation (pre-review, channel-text-only) cannot reach. Handoff conflated layers. Implementation already shipped via PR #1636 on 2026-05-02; what's open is just the PROPOSED → ACCEPTED status bump + a positioning paragraph. ~30 min of work pending user signoff.

### Filed for follow-up
- **#1684** — claude CLI dispatch ordering bug (closed by PR #1686).
- **#1685** — `tests/test_agent_runtime.py` worktree-incompatible `_TEST_PYTHON` (closed by PR #1686).
- **#1691** — reviewer false-positive Russianism guard (will close on PR #1692 merge).

---

## What's actively in-progress (DO NOT TOUCH)

- **PR #1686** — `claude-1684-prefer-npx-default` branch. Awaiting CI on commit `1f7196a7bb` + final Codex `[AGREE]` in thread `ecfc08bf223f` on channel `reviews`. Codex inbox is currently processing my re-review reply (lease until 00:38Z at handoff write time).
- **PR #1692** — `claude-1690-reviewer-fp-russianisms` branch. Awaiting CI + adversarial review (not yet dispatched — stop the next session from sending duplicate review requests; check `ab channel tail reviews` first).
- **#1683 (citation-provenance check)** — NOT yet implemented. The handoff's #1 priority. I deferred to after #1686/#1692 merged due to context budget. Strong empirical case from yesterday's deliberation, ACs documented, regression-test fixtures named. **This is the next priority for the next session.**
- **4 Gemini draft PRs** (#1687/#1688/#1689/#1690) — DRAFT for user review. Per-PR per-alert disposition in body. Do NOT auto-merge any of them — the user reviews license posture (Batch D's podcast HTML), security posture (Batch A's path-injection design), etc.

## Open architectural items inherited from predecessor (status update)

- **ADR-008 supersession question** — addressed via brief at `docs/decisions/pending/2026-05-05-adr-008-supersession-question.md`. Awaiting user signoff. Recommendation: option (a) keep as-is, status bump only.
- **Pin known-hallucination list to shared/context.md** — already done by predecessor's commit `f5edb3dbd8`. Marked complete.
- **HIST/OES seminar deliberation pilot** (handoff item #6) — NOT touched this session. Lower priority.

---

## Workflow lessons captured this session

1. **AGENTS.md:19 ban on `sys.executable` is load-bearing — even in docstrings and error messages.** I missed this rule when writing the #1685 piggyback fix. Codex caught it adversarially in two passes (first the runtime usage, then the literal token in docstring). Pre-submit checklist in AGENTS.md is enforced by reviewers, not just by automated grep — but a reviewer reading my code would tick the failed box. Lesson for next session: read AGENTS.md proactively before any non-trivial test/subprocess code.

2. **Handoff inheritance — verify before designing fixes around the framing** (memory rule #0G). The handoff's "ADR-008 still PROPOSED, awaits user signoff" was outdated — implementation merged via PR #1636 three days ago. The actual question was "scope down vs keep" not "accept vs reject." I caught this by reading the GH issue (#1632 closed by #1636) before writing the brief. The brief's recommendation pushes back on the handoff's "probably (b)" with concrete framing (the handoff conflated pre-review deliberation with post-write correction layers).

3. **Codex's literal-grep interpretation of style rules is sometimes too pedantic but cheap to comply with.** When the rule's spirit isn't violated but a strict reading is, just rephrase. 5 minutes vs an architectural debate. Worth it.

4. **Gemini dispatch produces DRAFT PRs reliably for security-class work.** All 4 batches landed PRs with proper per-alert dispositions. The brief format with explicit numbered worktree/test/PR steps + "do not auto-merge" instructions worked well. Save this brief format for future Gemini code-scanning dispatches.

5. **The `git rev-parse --git-common-dir` worktree fallback for `_TEST_PYTHON` is a clean general pattern.** Project-wide it could replace any other "find the project venv from inside a worktree" use. Possible future EPIC: standardize this resolver across other test/subprocess sites.

---

## Cold-start protocol for next session

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

# 1. Bootstrap from Monitor API
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

# 2. Verify clean main + check open PRs
git fetch origin main && git status -s && git log --oneline -5
gh pr list --author '@me' --state open
gh pr list --search 'gemini/codeql' --state open

# 3. Read THIS handoff + the predecessor:
#    docs/session-state/2026-05-05-overnight-autonomous-claude-cli-dispatch-fix-and-codeql-cleanup.md
#    docs/session-state/2026-05-05-deliberation-architecture-validated.md

# 4. Drain Codex inbox if anything pending
ab inbox show codex
# If pending: ab inbox run codex (in background)

# 5. Check #1686 / #1692 status — merge if both green and Codex [AGREE]
gh pr checks 1686
gh pr checks 1692

# 6. Surface ADR-008 supersession brief to user
ls docs/decisions/pending/

# 7. Resume #1683 (citation-provenance check) — TOP PRIORITY
gh issue view 1683
```

---

## Ranked next-session priorities

1. **Land #1686 + #1692** if not already merged. Both small PRs, mechanical work to merge once CI + review are green. Cleanup worktrees: `claude-1684-prefer-npx`, `claude-1690-reviewer-fp-russianisms`.

2. **Implement #1683 (citation-provenance check)** — the actual top priority from the previous handoff. Deferred this session due to context budget. Strong empirical case, ACs documented, regression-test fixtures named (the verbatim Gemini fake quote from threads `482884ca054e` and `7c6e401053bb`). This is the highest-leverage engineering work in the queue.

3. **User reviews 4 Gemini draft PRs** (#1687/#1688/#1689/#1690). Each is a separate batch with per-alert disposition in the PR body. Recommend reviewing in order B → C → D → A (B and C are lowest-risk warnings; A and D have higher-stakes security implications worth reviewing more carefully).

4. **Surface ADR-008 supersession brief** — `docs/decisions/pending/2026-05-05-adr-008-supersession-question.md`. Brief recommends option (a). 30 min to execute if user agrees.

5. **Re-dispatch #1665 (Holovashchuk ingest)** if user surfaces an alternative live PDF source. Comment on #1665 listed candidates: lounb.org.ua catalog, slovnyk.me linguistic_norm mirror, chtyvo.org.ua / diasporiana.org.ua / archive.org search.

6. **Audit other reviewer prompts** if #1692 merges cleanly. Same false-positive Russianism guard may benefit:
   - `scripts/build/phases/v6-review/v6-review-factual.md` (if it has Russianism logic)
   - `scripts/build/phases/v6-review/v6-review-honesty.md` (same)
   - `scripts/build/phases/v6-review-uk.md` (legacy V6 path)
   - `scripts/build/phases/linear-review-dim.md` (linear pipeline)

---

## Cross-thread notes (still active)

- **Codex weekly cap** still cleared (per predecessor handoff). Codex available for dispatches. Used 1 Codex this session (#1665, stopped on dead source) + 2 inbox-runner invocations for review processing. Within memory rule cap (max 2 in flight).
- **Gemini uncapped** — used 4 dispatches in parallel for code-scanning batches.
- **slovnyk.me license posture** unchanged; per-query fair use.
- **`~/.bash_secrets`** still where `GITHUB_TOKEN` lives; source manually before `gh` calls.
- **2 dispatch worktrees still alive at handoff:** `.worktrees/dispatch/gemini/codeql-A-path-injection`, `.worktrees/dispatch/gemini/codeql-B-secrets-exposure`, `.worktrees/dispatch/gemini/codeql-C-url-tag-validation`, `.worktrees/dispatch/gemini/codeql-D-js-html-xss`. These get cleaned up when their PRs merge (or when user closes the PRs unmerged). Codex dispatch worktree for #1665 was cleaned up post-handoff (no commits, dead source).
- **Memory rule #0F applied empirically** — Codex's review at AGENTS.md:19 traced to a specific source line, not a vibes-based "smells off." This is the correct adversarial-review pattern. Memory rule #0G applied to ADR-008 framing — verified the issue state before writing the brief.

---

## Statistics (final)

- **PRs opened by this session:** 7 (#1686, #1687, #1688, #1689, #1690, #1692, #1693)
- **PRs merged by this session:** 1 (#1693)
- **PRs in flight at session end:** 6 (#1686 awaiting fresh Codex `[AGREE]` post-rebase; #1687/#1688/#1689/#1690 draft for user security review; #1692 awaiting rebase onto current main + Codex review)
- **Issues filed:** 4 (#1684, #1685, #1691, plus a comment on #1665 reporting Codex's dead-PDF finding) + ADR-008 supersession brief in `docs/decisions/pending/`
- **Commits to my branches:** 3 commits on #1686 (after rebase: `25cc04af89` is the tip — Claude adapter fix + test_python git-common-dir resolver), 1 commit on #1692 (`70c2abf371`)
- **Adversarial review cycles:** 3 rounds with Codex on #1686 (3 blockers all addressed), fresh post-rebase request open at session end
- **Codex dispatches:** 1 (#1665 — stopped per dispatch's PDF-dead condition; worktree cleaned up)
- **Gemini dispatches:** 4 (CodeQL batches A/B/C/D — all completed, all produced draft PRs)
- **Token budget at session end:** ~340K (within 400K hard target)
- **Wall-clock duration:** ~70 min from session start to handoff write
