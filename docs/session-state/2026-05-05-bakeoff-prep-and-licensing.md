# Session Handoff — 2026-05-05 (bakeoff prep + licensing documentation)

> **Predecessor:** `2026-05-05-autonomous-top-of-list-drain.md`
> **Mode:** User-online second half of the day. Pivoted from queue-drain to bakeoff infrastructure after user clarified the writer-choice decision needs an empirical run, not a debate. Plus user-requested defensive licensing documentation.

---

## TL;DR — what shipped this half-session

### Merged (in order)

1. **`976160046a`** — `docs(licensing): add good-faith posture + expanded dictionary inventory` to `LICENSE-CONTENT.md`. Adds an explicit non-profit/non-commercial posture statement, an honest-mistake clause (rights-holders can flag concerns; offending content removed/paraphrased/attributed within 7 days), and the plain-language license tier breakdown the user articulated. Inventory expanded with the 7 dictionary additions since 2026-04-11 (ЕСУМ vol 1, slovnyk.me as СУМ-20 supersession, Гринчишин paronyms, Karavansky r2u, Holovashchuk pending, Ukrajinet quality caveat, СУМ-11 sovietization risk flag, Грінченко rename to `search_grinchenko_1907`).

2. **PR #1699 → main** (`069ab4f552`): `feat(telemetry): JSONL events for writer + reviewer prompt-adherence + tool calls`. Codex dispatch, 16-min duration, 1182+/3- across 3 files (`scripts/build/linear_pipeline.py` +835, `tests/test_linear_pipeline_telemetry.py` +316, `docs/MONITOR-API.md` +31). Adds 7 new event types: `writer_cot_emit`, `writer_tool_call`, `writer_end_gate`, `phase_writer_summary`, `reviewer_dim_evidence`, `reviewer_audit_call`, `phase_review_summary`. Existing event shapes immutable. Closes the telemetry prerequisite for the bakeoff.

3. **PR #1696 rebased onto main** (`d65d6b8a62`) — force-pushed to pick up #1699's telemetry. Bakeoff worktree at `.worktrees/dispatch/claude/1673-1661-cot-tier1-prompts/` now has both new V7 prompts AND the new telemetry events. CI re-running on rebased commit at handoff time.

4. **PR #1700 → main** (`2b09e082af`, merged 09:56:39Z): `feat(audit): bakeoff_aggregate.py — comparison matrix from telemetry events`. Codex dispatch, ~15-min duration. 1468+/0 across 2 files (`scripts/audit/bakeoff_aggregate.py` + `tests/test_bakeoff_aggregate.py`). Reads per-writer JSONL telemetry + .md outputs, emits `audit/bakeoff-{date}/REPORT.md` with 6 tables (prompt-adherence per writer, prompt-adherence per reviewer, content quality, tool usage, cross-reviewer bias, auto-findings). Bakeoff infrastructure complete.

---

## Bakeoff readiness state

Everything is in place for the user to run the A1/20 bakeoff:

| Prerequisite | State |
|---|---|
| New V7 prompts (#1696's CoT + Tier-1) | ✅ in worktree `.worktrees/dispatch/claude/1673-1661-cot-tier1-prompts/`, rebased onto telemetry |
| Telemetry events for prompt-adherence scoring | ✅ on main via #1699 (rebased into #1696's worktree) |
| Aggregator script | ✅ PR #1700 merged at 09:56:39Z |
| Plan for `a1/20` | ✅ `curriculum/l2-uk-en/plans/a1/my-morning.yaml` |
| Wiki packet for `a1/20` | ✅ `wiki/pedagogy/a1/my-morning.md` + `my-morning.sources.yaml` |
| Build commands documented | ✅ `docs/dispatch-briefs/2026-05-05-a1-20-bakeoff-with-new-prompts.md` |

The bakeoff is **fully runnable as of 09:56:39Z**. User runs the build commands per the brief; aggregator produces `audit/bakeoff-2026-05-05/REPORT.md`.

---

## Bakeoff design (recap from brief)

Three writers × cross-agent review × telemetry-driven scoring:

- **Writers:** Gemini 3.1-pro-preview, Claude Opus 4-7, GPT-5.5 (Codex CLI)
- **Reviewers:** cross-agent (each writer's output reviewed by the other two — no self-review)
- **Target module:** A1/20 `my-morning` (current POC, V7 era)
- **Evaluation dimensions:** prompt adherence (0-3 per sub-dim from telemetry), content quality (immersion / word count / naturalness / activity / vocab / plan adherence — A1-targeted), tool usage (calls per 100 words by tool)
- **Output:** `audit/bakeoff-2026-05-05/REPORT.md` — 6 tables, programmatic findings section

Per user 2026-05-05: "we need to do new bakeoff with the new prompts and see which llm follows the prompt best and creates the best content." Adherence + quality, both required for a writer to win.

---

## Licensing documentation update (defensive record)

Per user request 2026-05-05: "keep the licencing documented so we can show it in case something comes up and if we did mistake it was honest mistake since we didnt want to gain profit but help learners."

Added explicit good-faith section to `LICENSE-CONTENT.md` covering:

1. Non-commercial permanent posture (no revenue, ever — no ads, no premium, no paywall)
2. Educational purpose only (every source touched is for teaching Ukrainian L2 to English speakers)
3. Good-faith fair-use application (RAG retrieval context only, ≤200 chars per quote, transformative pedagogical use, attribution)
4. **Honest-mistake clause** (rights-holder can flag, offending content removed/paraphrased/attributed within 7 days)
5. Source-of-truth tracking commitment (every dictionary, textbook, blog, video, primary text listed in `LICENSE-CONTENT.md` with license tier; new sources update the doc in same PR)
6. Plain-language license tier definitions (public domain / free with attribution / fair use / all rights reserved)

Defensive record is now in `git log` — auditable history of how each source landed in the project, with license tier as we understood it at the time.

---

## Open at handoff write

- **PR #1696** (#1673+#1661 prompts) — DRAFT, rebased onto telemetry. User-pilot decision pending per user instruction "we wait" (until bakeoff results inform whether the new prompts actually work).
- **PR #1688** (XSS refactor) — DRAFT, deferred for the day. Workaround documented in predecessor handoff.
- **2 worktrees alive at handoff:** `claude/1673-1661-cot-tier1-prompts` (PR #1696), `gemini/codeql-D-js-html-xss` (PR #1688).

---

## Cold-start protocol for next session

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

# 1. Bootstrap from Monitor API
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

# 2. Verify clean main + sync
git fetch origin main && git pull --ff-only origin main && git status -s

# 3. Check #1700 (aggregator) status — likely merged by handoff arrival
gh pr view 1700 --json state,mergedAt
# If still open: gh pr checks 1700 ; merge if green
gh pr merge 1700 --squash --delete-branch

# 4. Clean up #1700's worktree post-merge
git worktree remove --force .worktrees/dispatch/codex/bakeoff-aggregator
git branch -D codex/bakeoff-aggregator

# 5. Read THIS handoff + the chain:
#    docs/session-state/2026-05-05-bakeoff-prep-and-licensing.md (this)
#    docs/session-state/2026-05-05-autonomous-top-of-list-drain.md (predecessor)
#    docs/session-state/2026-05-05-codeql-cleanup-and-adr008-resolution.md (further back)

# 6. The bakeoff is RUNNABLE. The brief at
#    docs/dispatch-briefs/2026-05-05-a1-20-bakeoff-with-new-prompts.md
#    has the user-runs-these commands. Ask the user when they want to fire
#    them; do NOT auto-fire (memory rule "BATCH COMMANDS — NEVER RUN, ONLY SUGGEST").
```

---

## Ranked next-session priorities

1. **Run the A1/20 bakeoff** (user-driven). 3 write commands + 6 review commands + aggregator. ~1 hour wall clock. Output: `audit/bakeoff-2026-05-05/REPORT.md`. This closes the writer-choice decision in `docs/decisions/2026-04-26-reboot-agent-responsibilities.md §3` AND validates whether the new V7 prompts work as designed.

2. **Decide on PR #1696 based on bakeoff** — if the new prompts produce demonstrably better content + adherence, merge. If not, the bakeoff itself tells us what to fix in the prompts.

3. **#1688 XSS refactor** — DRAFT PR deferred. Workaround documented. Low-leverage but should close the security-cleanup arc.

4. **#1666 paronym ingestion brief** — research done (NBU 1986 PDF OCR path). Brief writer + dispatch.

5. **#1663 Antonenko-Davydovych ingest** — local PDF + IA backup confirmed live. Mechanical PDF→FTS5 dispatch.

6. **#1664 Karavansky** — HTML scrape required (no API). Design scraper architecture.

7. **#1665 Holovashchuk** — needs alt source URL or drop the issue.

8. **slovnyk.me ingester** — replaces #1667 (close as superseded). Brief + dispatch.

9. **38 NEW CodeQL alerts** on the security tab — group by query class, dispatch in 4-6 batches.

10. **A1 strategic redirect** — still pending from earlier handoffs. Needs Monitor API state scan + ONE concrete A1 proposal. User-judgment.

---

## Lessons captured this half-session

1. **Telemetry standalone, not coupled to prompt diff.** Codex's #1699 instrumentation landed as its own PR — reviewable independently of #1696's prompt diff. After merge, #1696 rebased to pick up the telemetry. Two independent reviews, one combined runtime. Cleaner than bundling.

2. **Prompt adherence ≠ content quality.** The bakeoff explicitly scores both as separate axes. A writer that produces beautiful content while bypassing the CoT scaffolding is failing differently than a writer that follows CoT scrupulously but produces mediocre content. Both are losses; the diagnosis is different.

3. **Cross-reviewer bias requires cross-agent matrix.** Each writer reviewed by the other two (no self-review) makes inter-model bias visible — if Claude over-rates Claude, the matrix shows it; the aggregator's auto-findings flag systematic over-rating per family.

4. **`--hard-timeout` bumped to 4500s for substantive Codex briefs.** Memory note from predecessor's #1680 hard-timeout case — at 60min Codex got the commit done but couldn't push + open PR. 75min headroom prevents that recurrence. #1699 (16min) and #1700 (~15min) both finished comfortably.

5. **Defensive licensing documentation is a 5-min task that pays compound dividends.** The good-faith section is now in git history; if a rights-holder ever raises a concern, the response is "see LICENSE-CONTENT.md, here's the honest-mistake clause and contact path." Auditable record beats handwavy intent.

---

## Statistics

- **PRs merged this half-session:** 2 (#1699, #1700) + 1 documentation commit (`976160046a`)
- **PRs in flight at handoff:** 0
- **PRs DRAFT awaiting user pilot:** 1 (#1696, rebased + ready)
- **PRs DRAFT deferred:** 1 (#1688)
- **Codex dispatches:** 2 (#1699 telemetry, #1700 aggregator) — both successful, both within bumped 75-min hard-timeout
- **Wall-clock duration:** ~70 min from "you can continue we have 28% context" to handoff write
