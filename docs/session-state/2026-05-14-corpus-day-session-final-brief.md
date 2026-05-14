---
date: 2026-05-14
session: "Full day session — corpus C3 (ULP) shipped, content-indexing audit triggered by user concern, 1240-orphan textbook_sections gap fixed, C2 (Ohoiko 500+ verbs) shipped. User off to work for most of the session; orchestrator drove autonomously per #M-6."
status: ok
main_sha: f4a48d2645
main_green: true
open_prs: []
active_dispatches: 0
agents: [claude, codex, gemini]
worktrees_open: 4  # main + codex-interactive (detached, Codex active) + 3 with unmerged WIP
ci_notes: "All 4 shipped PRs (#1981, #1982, #1983, #1984) passed blocking checks. Advisory `review / review` (Gemini Dispatch) failed on each — non-blocking per #M-0.5."
filed_today: []
merged_today: [1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984]  # 9 PRs total across the day
closed_today: [1969]  # via #1974
next_p0: |
  1. C4 (Pohribnyi book OCR) — BLOCKED. Place 52MB image-PDF in
     docs/references/private/ to unblock. Tesseract 5.5.2 + ukr lang
     verified available. Once unblocked: same _section_coverage pattern
     as C2/C3.
  2. 3 unmerged worktrees need user decision (see "Unmerged WIP" below)
  3. Task B (textbooks.page column) — separate large session,
     unblocks m20 build #5 textbook_grounding gate (#1975)
---

# Brief — 2026-05-14 final — corpus C3+C2 shipped, content-indexing gap fixed

> Predecessors:
> - `2026-05-14-corpus-completion-night-brief.md` (overnight predecessor)
> - `2026-05-14-content-indexing-audit-brief.md` (mid-session snapshot via PR #1983)
>
> This brief is the final state-of-day record.

## TL;DR

**Nine PRs landed today** across two sessions (overnight + day). Four
from this day session, autonomously driven while the user was at work:

| PR | Status | What |
|---|---|---|
| **#1981** | ✅ merged | C3 — ULP lesson-notes ingester. 240 lessons × 6 seasons → textbooks. |
| **#1982** | ✅ merged | textbook_sections backfill: 1,240 orphan chunks (Ohoiko 1000-words + 6 ULP books) gained section coverage. Shared `_section_coverage` helper. Both ingesters write sections natively going forward. |
| **#1983** | ✅ merged | Mid-session handoff brief. |
| **#1984** | ✅ merged | C2 — Ohoiko 500+ verbs ingester. Page-based parser. 500 verbs with conjugation tables. |

User trigger mid-session: *"make sure after everything ingested that
all our content is indexed, i don't know why we missed indexes on our
already ingested contents"* — answered by the audit + #1982 fix.

## Corpus state at session end

```
$ sqlite3 data/sources.db "SELECT COUNT(*) FROM textbooks; SELECT COUNT(*) FROM textbooks_fts; SELECT COUNT(*) FROM textbook_sections"
25517
25517    -- FTS in sync ✓
6811     -- (was 5071 at start; +1740: 1240 backfill + 500 new verbs)
```

```
Today's new reference materials, all 100% section-linked:

  anna-ohoiko-1000-words-2nd-ed   1000 chunks   1000/1000 section-linked
  anna-ohoiko-500-verbs            500 chunks    500/500 section-linked   ← NEW (C2)
  ulp-1-00-lesson-notes             40 chunks     40/40 section-linked
  ulp-2-00-lesson-notes             40 chunks     40/40 section-linked
  ulp-3-00-lesson-notes             40 chunks     40/40 section-linked
  ulp-4-00-lesson-notes             40 chunks     40/40 section-linked
  ulp-5-00-lesson-notes             40 chunks     40/40 section-linked
  ulp-6-00-lesson-notes             40 chunks     40/40 section-linked
                                  -----
                                  1,740 chunks
```

## Content-indexing audit (user question answered)

| Subsystem | Status | Detail |
|---|---|---|
| FTS shadow tables (5) | ✅ all in sync | textbooks (25,517), ukrainian_wiki (22,385), wikipedia (1,026), literary_texts (137,688), external_articles (1,205) |
| Dictionary b-tree indexes (9) | ✅ all indexed | balla_en_uk, dmklinger_uk_en, frazeolohichnyi, grinchenko, puls_cefr, style_guide, sum11, ukrajinet, wiktionary — each with `idx_*_word` index for direct lookup |
| VESUM (separate DB) | ✅ | 6,691,276 forms in `data/vesum.db` |
| textbook_sections for Ohoiko + ULP | ❌→✅ FIXED | 1,240 orphans → 0 via #1982 backfill |
| Seminar primary source | ✅ | literary_texts: 137,688 chunks, 3,278 distinct works, FTS in sync |
| ukrainian_wiki track aliasing | ✅ intentional | track column stores DOMAIN names (figures/works/historiography/periods/etc.); curriculum tracks (bio/lit/hist/istorio) READ multiple domains via `TRACK_DOMAINS` in `scripts/wiki/config.py:101-115` |

### Spillover orphans (NOT in scope of #1982)

After the backfill, **280 orphans remain** across ~15 school textbooks
(1-18% per book). These are `extract_sections.py` gaps where the
school-textbook pipeline didn't find structural markers for specific
chunks. Not blocking; would need an `extract_sections.py` enhancement
to address. Not filed yet.

## Architectural changes encoded

| Where | Rule |
|---|---|
| `scripts/ingest/_section_coverage.py` (PR #1982) | Shared helper for lesson-style ingests (1:1 chunk:section). Idempotent on (source_file, section_title). `grade=0` sentinel for non-school reference material. |
| `scripts/ingest/ohoiko_books_ingest.py` (PR #1982) | Writes sections natively. `--force` deletes sections too. |
| `scripts/ingest/ulp_lesson_notes_ingest.py` (PR #1982) | Writes sections natively. `--force` deletes sections too. |
| `scripts/ingest/ohoiko_verbs_ingest.py` (PR #1984) | New page-based parser (form-feed + №N markers). Uses `_section_coverage` from day 1. |
| `scripts/ingest/backfill_lesson_sections.py` (PR #1982) | One-shot remediation for existing orphans. Idempotent. |

## Remaining task queue

| Task | Status | Notes |
|---|---|---|
| **C4** Pohribnyi book OCR | BLOCKED | Source PDF not in `docs/references/private/`. Brief from previous session mentioned 52MB image-PDF (CorelDRAW 2010), but file isn't on disk. **User: place file** to unblock. Tesseract 5.5.2 + ukr lang verified. Once unblocked, ~150 LOC ingester using same `_section_coverage` pattern. |
| **B** textbooks.page column | unstarted | Separate large session — schema migration + chunking pipeline change + full backfill from PDFs. Unblocks textbook_grounding gate (#1975 m20 build #5). |
| **#1975** m20 build #5 gate failures | filed | vesum_verified writer-output errors + textbook_grounding page-matcher gap. Phase 2b m01-m07 batch paused. |
| Section-extraction spillover (280 chunks) | not filed | ~15 school textbooks have 1-18% orphan chunks where `extract_sections.py` didn't find markers. Filing left as a follow-up. |

## Unmerged WIP — needs user decision

After cleanup this session removed 5 fully-merged build worktrees from
yesterday's m20 iterations. Three worktrees with unmerged commits
remain on disk:

```
.worktrees/dispatch/claude/bakeoff-2026-05-12-night
  └─ 5a72a31f9b  test(bakeoff): claude-tools vs codex-tools on a1/my-morning (2026-05-12 night)
     Decision REVISED → claude-tools per session brief 2026-05-13. Likely
     historical reference data only. SAFE to delete if you don't need
     the bakeoff transcript.

.worktrees/dispatch/claude/writer-prompt-tune-2026-05-13
  └─ ce7ca40881  fix(writer-prompt): budget + citation + immersion discipline for V7 claude-tools writer
     Predates #1974 which closed #1969. Either superseded or
     complementary — review the diff. If superseded, delete; if useful,
     open a follow-up PR.

.worktrees/dispatch/codex/pass2-only-contract-test-2026-05-13
  └─ 5e65230c3f  experiment(twopass): add pass2-only contract test
     Codex experimental work. Status unclear without Codex context.
     Probably safe to leave for Codex to clean up next session.
```

And one worktree to LEAVE ALONE:

```
.worktrees/codex-interactive  (detached HEAD)
  └─ Active Codex interactive session. Don't touch.
```

## How to clean the WIP worktrees (if user OKs)

```bash
# bakeoff (likely safe — decision is settled)
git worktree remove --force .worktrees/dispatch/claude/bakeoff-2026-05-12-night
git branch -D claude/bakeoff-2026-05-12-night

# writer-prompt-tune (only after reviewing diff vs #1974)
git diff main...claude/writer-prompt-tune-2026-05-13 -- 'scripts/build/prompts/*.md'
# If superseded:
git worktree remove --force .worktrees/dispatch/claude/writer-prompt-tune-2026-05-13
git branch -D claude/writer-prompt-tune-2026-05-13

# codex pass2 — leave to Codex session
```

## Pre-commit backup files (1.5GB each, ungitignored, untracked)

```
data/sources.db.bak-20260513-224311-pre-channel-id-fix   (from #1976)
data/sources.db.bak-20260514-062125-pre-section-backfill (from #1982)
data/sources.db.bak-20260514-*-pre-verbs-ingest          (from #1984)
```

Three pre-modification snapshots accumulated today. Keep at least the
most recent (`pre-verbs-ingest`) until C4 lands or a fresh major DB
modification is queued. Earlier ones can be deleted to reclaim ~3GB.

## Next session opening action

1. Read this brief.
2. Confirm main is current: `git log -1 --oneline` should show
   `f4a48d2645` or newer.
3. Decide on the 3 unmerged WIP worktrees (review-then-remove pattern
   above).
4. If user has placed the Pohribnyi book PDF, start C4. Pattern:
   ```bash
   tesseract docs/references/private/<pohribnyi.pdf>.png stdout -l ukr
   # then ingest using _section_coverage helper, 1:1 chunk/section mapping
   ```
5. Otherwise — consider Task B (textbooks.page column) — significant
   work but unblocks m20 builds.

## Worktrees on disk at handoff

```
$ git worktree list
main                                                       7fb39c... → f4a48d... [main]
.worktrees/codex-interactive                              ffafa6a60e (detached HEAD)
.worktrees/dispatch/claude/bakeoff-2026-05-12-night       5a72a31f9b [claude/bakeoff-2026-05-12-night]
.worktrees/dispatch/claude/writer-prompt-tune-2026-05-13  ce7ca40881 [claude/writer-prompt-tune-2026-05-13]
.worktrees/dispatch/codex/pass2-only-contract-test-2026-05-13  5e65230c3f [codex/pass2-only-contract-test-2026-05-13]
```

5 build worktrees from yesterday's m20 iterations: removed in this
session's hygiene pass (all branches merged or empty).

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier
handoffs". MD-only per #M-2 ai→ai.*
