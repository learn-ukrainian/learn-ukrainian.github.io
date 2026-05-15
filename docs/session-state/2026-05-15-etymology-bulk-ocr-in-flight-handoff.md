---
date: 2026-05-15
session: "Etymology Phase 2 bulk OCR running in background; #1975 matcher fix merged. User pivoting focus to A1 work via /clear (no restart). Next orchestrator: PROTECT the running OCR script + drive A1 build queue (now unblocked) in foreground."
status: green
main_sha: c80a29f9b5
main_green: true
open_prs: [1997, 2000, 1873]
active_dispatches: 1  # bulk OCR running locally as background bash, NOT a delegate.py dispatch
worktrees_open: 6  # main + 4 user/other-agent + 1 active bulk-OCR worktree
agents: [claude, codex, gemini]
ci_notes: "Main at c80a29f9b5 (push includes #1975 merge + 4 hygiene commits). PR #1873 stale dependabot, #1997 user-owned, #2000 depends on #1997. Etymology Phase 2 PR not opened yet — gated on bulk OCR completing across multiple account rotations."
filed_today: []
merged_today: [2005, 1999, 2004]
closed_today: []
next_p0: |
  PIVOT TO A1 WHILE ETYMOLOGY PROCESSES IN BACKGROUND.

  CRITICAL — DO NOT TOUCH:
  1. Running Python process: pid 63864 (`/Users/.../.venv/bin/python -u
     scripts/etymology/bulk_ocr_gemini.py --concurrency 4 --rpm 12
     --model auto`). It is the bulk OCR for ESUM volumes.
  2. Worktree: `.worktrees/dispatch/codex/etymology-phase-2-bulk-ocr-codex-2026-05-15/`.
     The script reads/writes inside this worktree and to
     `data/raw/esum/jp2-staging/` (the 2 GB of JP2 ZIPs, symlinked from main).
  3. The bulk-run log at the worktree's
     `audit/etymology-ocr-feasibility/bulk-run-log.jsonl` is the source of
     truth for OCR progress.

  WHAT TO DO IN FOREGROUND — A1:
  - PR #2005 merged the textbook_grounding matcher fix (chunk_id lookup
    for `Author Grade N, p.M` references). The m20 `corpus_missing` halt
    is unblocked.
  - But m20 ALSO has a `vesum_verified` malformed-forms failure (writer
    emitted `ди_юся`, `дивюся`, `користуювася`) per #1975 §3. Separate
    bug, writer-prompt scope. That fix is the next action for A1.
  - Plus: the plan_references for `a1/my-morning` cite wrong-LEVEL
    textbooks (Караман Grade 10 p.187 is slang lexicon, not morning
    routines; Захарійчук Grade 4 is not in corpus — Grade 1 is).
    Likely needs a plan-review pass to swap to actual A1-appropriate
    sources before rebuilding m20.
  - Standing A1 P0 chain from prior briefs: m20 → m01-m07 batch.

  WHAT TO WATCH FOR (background):
  - Bulk OCR will eventually hit Gemini daily quota (~1,500 pages per
    account) and emit `{"event":"QUOTA_HALT","page":"vol{N}/p{NNNN}"}` to
    bulk-run-log.jsonl. When you see that: alert user to rotate Gemini
    OAuth account, then restart the script (idempotent).
  - The script's patched regex catches `TerminalQuotaError /
    QUOTA_EXHAUSTED / quota will reset after Nh` cleanly now.
  - Other halts to watch: `BULK_QUALITY_HALT` (>20% error rate in last
    100 pages). Threshold tuned 5→20 this session because Gemini Free
    Tier has ~10-15% baseline transient burst rate.
  - May also see Gemini server-overload errors ("No capacity available
    for model gemini-2.5-flash on the server"). The `--model auto`
    switch helps because the CLI's ModelRouterService falls back to
    other models when one is overloaded.
---

# Brief — 2026-05-15 — etymology bulk OCR in flight, pivot to A1

> Predecessor: `2026-05-15-etymology-shipped-but-broken-brief.md` (this
> session opened from there; etymology Phase 1 was diagnosed broken, fixed
> via Gemini-Vision feasibility test PR #2004, bulk re-OCR fired Phase 2
> which is what's running now).

## TL;DR

The user is going to `/clear` (NOT restart). Next session takes over with:
- The bulk OCR for ESUM volumes running in a background Python process.
  Touching/killing it loses work.
- A1 build queue NEWLY unblocked by PR #2005 (#1975 matcher fix).
- User wants A1 to be the active foreground work while etymology processes.

## What's already done this session

### Code changes shipped to main

| PR | What | Status |
|---|---|---|
| #1999 | Russianism eval harness v1 (prior session's overnight work, sat green; merged today) | ✅ merged |
| #2004 | Etymology Phase 1 OCR feasibility — Gemini Vision wins (≥95% cognate recovery) | ✅ merged |
| #2005 | #1975 fix: textbook_grounding matcher does chunk_id lookup for `Author Grade N, p.M` refs | ✅ merged |
| `c80a29f9b5` direct commit | Plus 4 docs/chore commits: dispatch briefs, audit jsonls, gitignore patches | ✅ on main |

### In-flight work — etymology Phase 2

**Worktree:** `.worktrees/dispatch/codex/etymology-phase-2-bulk-ocr-codex-2026-05-15/`
**Branch:** `codex/etymology-phase-2-bulk-ocr-codex-2026-05-15` (no commits yet — work in dirty tree)
**Script:** `scripts/etymology/bulk_ocr_gemini.py` (written by Codex this session, never committed)

Patches applied to Codex's script during run:
- `DAILY_QUOTA_RE` regex now catches `TerminalQuotaError` / `QUOTA_EXHAUSTED` / `quota will reset after Nh` (covers Gemini CLI 0.42's actual classifyGoogleError output).
- `ROLLING_ERROR_LIMIT` raised 5 → 20 (Gemini Free Tier has ~10-15% baseline transient burst rate; 5% threshold halted too aggressively).
- Added `is_low_quality_output()` check: rejects .md outputs <500 bytes or dominated by `<ctrl\d+>` markers (caught ~3.8% silent-failure rate where gemini-cli returned exit 0 with garbage).
- Added `strip_planning_preamble()`: removes two leak families before writing .md:
  1. 2.5-flash `<ctrl46>...update_topic{strategic_intent:...page number at the (end|bottom).`
  2. auto/3.x conversational `"Wait! I can see the image now. Let me transcribe..."`
  Universal heuristic: skip leading lines until first line with ≥3 consecutive Cyrillic letters.

**Pages OCR'd so far this run:** 691 ok / 130 errors (combined across multiple restart cycles).
**Valid .md files on disk:** 647.
**Total to OCR:** 3,691.
**Throughput observed:** ~4 pages/min on 2.5-flash, dropping to ~2.5 pages/min with server overload.

### Account rotation history this session

1. First account hit daily quota after ~548 OK pages. User rotated.
2. Second account on `gemini-2.5-flash` started fine then hit "No capacity available for model gemini-2.5-flash on the server" (Google server-side overload, not account quota).
3. Switched to `--model auto` (Gemini CLI's ModelRouterService); router tries gemini-3.1-pro-preview first, falls back to working model when no capacity. Quality on test page = all cognates exact.

The current run uses `--model auto`. Watch the bulk-run-log.jsonl for quota events.

## Process pid + how to restart if it dies

If pid 63864 dies cleanly with `BULK_QUALITY_HALT` or `QUOTA_HALT`:
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/etymology-phase-2-bulk-ocr-codex-2026-05-15
.venv/bin/python -u scripts/etymology/bulk_ocr_gemini.py --concurrency 4 --rpm 12 --model auto > /tmp/bulk-ocr-run.log 2>&1 &
```

The script is idempotent — re-running skips pages with existing .md output. Don't worry about over-running.

If you need to STOP it (e.g. user wants to take Gemini quota for something else):
```bash
pkill -f bulk_ocr_gemini.py
```

## What's NOT done — Phase 2 closeout (gated on bulk OCR completing)

After all 3,691 pages are OCR'd across multiple account rotations:
1. Concatenate per-page `.md` files into `data/raw/esum/vol{N}-gemini.txt`
2. Re-ingest via `scripts/ingest/esum_ingest.py --source-suffix gemini --replace`
3. Tighten `scripts/etymology/extract_cognate_forms.py` regex (reject digits + VESUM-function-words)
4. Rebuild `starlight/src/data/etymology-manifest.json` (~27 MB)
5. Strip fabricated featured-card glosses in `starlight/src/pages/etymology/index.astro`
6. 20-entry deterministic-random spot-check (seed=2001)
7. Commit, push, open PR — DO NOT auto-merge

Each step is documented in `docs/dispatch-briefs/2026-05-15-etymology-phase-2-codex.md`.

## A1 P0 — what to attack in the foreground

Per the standing carry-over from earlier briefs:

### Step 1 — investigate m20's `vesum_verified` malformations

#1975 §3 reports the writer emitted `ди_юся`, `дивюся`, `користуювася` — these are real writer errors, not gate bugs. The pre-emit checklist (PR #1974) DID activate (4 verify_words calls logged). So either:
- VESUM lemma resolution failed silently for these forms
- The writer emitted them in a section that bypassed verification
- The writer prompt's malformation patterns aren't covered

Steps:
1. Read the m20 writer output: `.worktrees/builds/a1-my-morning-20260513-221945/curriculum/l2-uk-en/a1/my-morning/*.md` (or wherever the latest m20 build artifacts live — check `curriculum/l2-uk-en/a1/my-morning/status/` for pointers)
2. Find where the malformed forms appear in the writer output
3. Determine why VESUM didn't catch them in the pre-emit pass
4. Decide: writer-prompt patch OR gate-tighten OR both

### Step 2 — re-check the plan_references

This session's #1975 diagnostic surfaced that `a1/my-morning/resources.yaml` cites wrong-level textbooks:
- Караман Grade 10, p.187 → slang lexicon, not morning routines
- Захарійчук Grade 4, p.162 → Grade 4 not in corpus (Grade 1 is)
- Кравцова Grade 4, p.113 → check what's there

The actual A1 morning-routine content lives in `1-klas-bukvar-zaharijchuk-2025-1_s0101` ("Золотий Зайчик прокинувся і невдоволено позіхнув...") and similar Grade 1 entries. Need a plan-review pass to swap to A1-appropriate sources before rebuilding m20.

### Step 3 — rebuild m20 and verify GREEN

Once writer + plan-references are fixed:
```bash
.venv/bin/python scripts/build/v7_build.py a1 my-morning --worktree
```

Watch via Monitor tool on the JSONL events.

### Step 4 — unlock m01-m07 batch

Per the standing brief chain, Phase 2b A1 batch (m01-m07) is paused on m20 GREEN. After m20 ships clean, the batch can resume.

## Open PRs (background)

- **#1997** (user-owned, `feat/russicism-ua-gec-patterns`) — leave alone.
- **#2000** (UA-GEC bulk lookup) — depends on #1997, also had an unrelated `tests/wiki/test_ukrainian_wiki_corpus.py` pytest fail. Leave until #1997 lands.
- **#1873** (stale dependabot starlight bump) — frontend build fails, low priority, leave.

## Open issues (background)

- **#2001** — etymology re-OCR. In flight via Phase 2; will close after the post-OCR PR lands.
- **#1975** — m20 build #5 RED. Half-resolved (matcher fix shipped); the `vesum_verified` malformation is the remaining work.
- **#1969**, **#1960**, **#1942** — older queue, not blocking.

## Worktrees alive at handoff

```
main                                                                              c80a29f9b5 [main]
.worktrees/cache-test-fix                                                         9c60253a26 [fix/cache-test-isolation]   ← user/other
.worktrees/codex-interactive                                                      2eb62691d4 (detached HEAD)              ← user/other
.worktrees/dispatch/codex/etymology-phase-2-bulk-ocr-codex-2026-05-15             ACTIVE BULK OCR                          ← DO NOT TOUCH
.worktrees/dispatch/codex/pr2-ua-gec-bulk-lookup-2026-05-15                       ba8602e7af [codex/pr2-ua-gec-bulk-lookup] ← PR #2000
.worktrees/eval-run-2026-05-14                                                    bff4c23463 [codex/eval-harness-v1-2026-05-15] ← user uncommitted eval run
.worktrees/russicism-ua-gec                                                       f582f50649 [feat/russicism-ua-gec-patterns]   ← PR #1997, user-owned
```

Plus local-only branch `wip/a1-landing-refactor` (commit `062e874ddc`) — prior session's A1 landing page WIP, parked off-main during today's hygiene pass.

## Monitor / wakeup state (will NOT survive /clear)

The next session must re-arm these:
- A `Monitor` tail on `bulk-run-log.jsonl` filtering for `QUOTA_HALT|BULK_QUALITY_HALT|summary`:
  ```
  tail -F .worktrees/dispatch/codex/etymology-phase-2-bulk-ocr-codex-2026-05-15/audit/etymology-ocr-feasibility/bulk-run-log.jsonl 2>/dev/null | grep --line-buffered -E '"event":"(QUOTA_HALT|BULK_QUALITY_HALT|summary)"'
  ```
- A `ScheduleWakeup` heartbeat every 30-45 min (poll line count + recent events; alert on halt).

## #M-* lessons reinforced this session

- **#M-4 (deterministic over hallucination):** I called out my own use of "русизм" (the older / Russian-leaning term) when the modern term is "росіянізм". User had to correct me. The wiki/textbook scans I ran missed `росіянізм` initially because I only grepped `русизм`; expanding to both gave 22 vs 2 hits, confirming modern texts use росіянізм 11× more often. Encode in next session's wiki-russianism work.
- **#M-5 (never print secrets):** Maintained — no credentials printed.
- **#M-6 (drive the project, don't defer):** Mostly held. User had to nudge me twice on (a) stripping the русизм concept instead of asking for the correct mini-model name (which was `gpt-5.4-mini`, not `gpt-5.5-mini` which doesn't exist), and (b) the wiki-russianism hypothesis misreading. Both were "delete and continue" failures where ASK was the right move.
- **#M-8 (orchestrator-active through dispatch lifecycle):** Held during dispatch monitoring; QUOTA_HALT response was prompt. Pivoting to A1 in next session must NOT mean abandoning the OCR — wakeups + Monitor must keep watch.

## How to start the next session

1. Read this brief.
2. Re-arm the Monitor + ScheduleWakeup per the snippets above.
3. Confirm pid 63864 (or its successor — `pgrep -f bulk_ocr_gemini`) is alive and processing.
4. Start A1 m20 investigation per the "A1 P0" section.
5. When QUOTA_HALT or BULK_QUALITY_HALT fires: alert user, follow restart procedure.
6. When all 3,691 pages OCR'd: execute the Phase 2 closeout checklist.

---

*Format: MD per #M-2 (ai→ai). Companion: `claude_extensions/rules/workflow.md` §
"Two-tier handoffs".*
