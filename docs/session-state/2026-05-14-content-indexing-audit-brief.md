---
date: 2026-05-14
session: "Day session — corpus C3 (ULP) ingest + user-flagged content-indexing audit. Built ULP ingester (PR #1981, merged), then user asked 'make sure all content is indexed — why did we miss indexes on already-ingested content?'. Comprehensive audit found 1,240 textbook_sections orphans across Ohoiko 1000-words + 6 ULP books. Fix in PR #1982 (CI pending at handoff)."
status: ok
main_sha: 7bf35ca1e3
main_green: true
open_prs: [1982]
active_dispatches: 0
agents: [claude, codex, gemini]
worktrees_open: 5  # main + 1 section-coverage PR + 5 stale build worktrees from yesterday's m20 + 3 stale dispatch worktrees (all branches merged/abandoned)
ci_notes: "PR #1982 CI pending — Test (pytest) still running at handoff. Other blocking checks already green. Advisory `review / review` fail expected (Gemini Dispatch noise, non-blocking per #M-0.5)."
filed_today: []
merged_today: [1981]
closed_today: []
next_p0: |
  1. Merge PR #1982 when Test (pytest) goes green
  2. Clean section-coverage worktree + branch
  3. Begin C2 (Ohoiko 500+ Verbs) — design ready
  4. C4 (Pohribnyi book OCR) is BLOCKED: source PDF not in docs/references/private/
     (the brief mentioned a 52MB image-PDF but it's not on disk). User must
     provide before C4 can start.
---

# Brief — 2026-05-14 — content-indexing audit (1240 orphan chunks fixed)

> Predecessor: `2026-05-14-corpus-completion-night-brief.md`. This session
> completed C3 (ULP ingest, PR #1981 landed), then pivoted to a
> comprehensive content-indexing audit triggered by user concern.

## TL;DR

Two PRs in flight:

| PR | Status | What |
|---|---|---|
| **#1981** | ✅ merged 7bf35ca1e3 | ULP lesson-notes ingester. 240 lessons across 6 seasons inserted into textbooks. 31 unit tests. |
| **#1982** | 🟡 open, pytest pending | textbook_sections backfill for 1,240 orphans (Ohoiko 1000-words + 6 ULP). Helper + ingester updates + one-shot backfill + 10 tests. |

User trigger: *"make sure after everything ingested that all our content
is indexed, i don't know why we missed indexes on our already ingested
contents"* (2026-05-14 morning). Audit found the gap; PR #1982 fixed it.

## Comprehensive content-indexing audit

| Subsystem | Status | Detail |
|---|---|---|
| FTS shadow tables (5) | ✅ all in sync | textbooks (25,017), ukrainian_wiki (22,385), wikipedia (1,026), literary_texts (137,688), external_articles (1,205) |
| Dictionary b-tree indexes (9) | ✅ all indexed | balla_en_uk, dmklinger_uk_en, frazeolohichnyi, grinchenko, puls_cefr, style_guide, sum11, ukrajinet, wiktionary |
| VESUM (separate DB) | ✅ | 6,691,276 forms in `data/vesum.db` |
| textbook_sections for school books | ✅ | 5,071 sections; ~179 spillover orphans (1-18% per book, normal `extract_sections.py` gaps) |
| textbook_sections for Ohoiko + ULP | ❌→✅ | 1,240 orphans backfilled in PR #1982: now 0 |
| Seminar primary source | ✅ | literary_texts: 137,688 chunks across 3,278 works, FTS in sync |
| ukrainian_wiki track-name mismatch | ✅ non-issue | Track column stores domain names (figures/works/historiography/periods/etc.); curriculum tracks (bio/lit/hist/istorio) read multiple domains via TRACK_DOMAINS in scripts/wiki/config.py:101-115. Intentional aliasing. |

## What was broken (PR #1982 root cause)

`scripts/wiki/sources_db.py:208` `_search_sections_fts5` filters
`s.parent_section_id IS NOT NULL` — chunks without a parent section are
invisible to section-level retrieval.

`scripts/wiki/extract_sections.py` is designed for school-textbook PDFs
(markers like `§ N`, `Сторінка N`, `Розділ N`). It does NOT produce
sections for lesson-style books (Anna Ohoiko word lists, Ukrainian
Lessons Podcast lesson notes). Both PR #1977 (Ohoiko, 2026-05-14
morning) and PR #1981 (ULP, 2026-05-14 morning) wrote only to
`textbooks`, leaving all 1,240 of their chunks orphaned.

## Fix architecture (PR #1982)

- **NEW** `scripts/ingest/_section_coverage.py` — shared helper.
  `LessonSection` dataclass + `link_lesson_sections()` + defensive
  `ensure_section_schema()`. Idempotent on `(source_file, section_title)`.
  Uses `grade=0` sentinel for non-school reference material (school
  books occupy grades 1-11).
- `ohoiko_books_ingest.py` writes sections natively (`Entry N: <headword>`)
- `ulp_lesson_notes_ingest.py` writes sections natively (matches chunk title)
- **NEW** `scripts/ingest/backfill_lesson_sections.py` — one-shot
  remediation for the existing 1,240 orphans.
- 10 unit tests in `tests/test_section_coverage.py`.

## Canonical DB state (after PR #1982 backfill)

```
$ sqlite3 data/sources.db "SELECT COUNT(*) FROM textbook_sections; SELECT COUNT(*) FROM textbooks WHERE parent_section_id IS NULL"
6311   -- was 5071 before; +1240
280    -- whole-DB orphans; was 1419 before; +179 spillover remain (school books, not in scope)
```

Per-source coverage after backfill:
```
anna-ohoiko-1000-words-2nd-ed: 1000 chunks → 1000 sections, 0 orphan
ulp-1-00-lesson-notes:           40 chunks →   40 sections, 0 orphan
ulp-2-00-lesson-notes:           40 chunks →   40 sections, 0 orphan
ulp-3-00-lesson-notes:           40 chunks →   40 sections, 0 orphan
ulp-4-00-lesson-notes:           40 chunks →   40 sections, 0 orphan
ulp-5-00-lesson-notes:           40 chunks →   40 sections, 0 orphan
ulp-6-00-lesson-notes:           40 chunks →   40 sections, 0 orphan
```

Section-level retrieval probe (was 0 hits for these source_files before fix):
```
MATCH 'Стус' (ulp%):
  section_id=6436 ulp-4-00: Lesson 160: Василь Стус, шістдесятники та дисиденти
  section_id=6503 ulp-6-00: Lesson 227: Українська поезія. Василь Симоненко...
MATCH 'автобус' (anna-ohoiko-1000-words-2nd-ed):
  section_id=5279 Entry 3: авто́бус
```

DB backup before backfill: `data/sources.db.bak-20260514-064136-pre-section-backfill` (1.5GB).

## Remaining task queue (post #1982)

| Task | Status | Notes |
|---|---|---|
| **C2** Ohoiko 500+ Verbs ingester | unstarted | Different parser shape: `№ NNN` markers preceded by `\x0c` form-feed page breaks. 499 verb pages from #1..#500, missing #211 (PDF extraction quirk). Each verb page has full conjugation tables + examples. Use new `_section_coverage.py` helper so sections land natively. |
| **C4** Pohribnyi book OCR | BLOCKED | Source PDF not in `docs/references/private/`. Need user to place 52MB image-PDF there. Tesseract 5.5.2 + ukr lang model verified available. |
| **B** textbooks.page column | unstarted | Separate large session. Unblocks m20 textbook_grounding gate (#1975). |
| **#1975** m20 build #5 gate failures | filed | vesum_verified writer-output errors + textbook_grounding page-matcher gap. Phase 2b m01-m07 paused. |

## Decisions encoded

| Where | Rule |
|---|---|
| `scripts/ingest/_section_coverage.py` (PR #1982) | Every lesson-style ingester (1:1 chunk:section mapping) writes via `link_lesson_sections()`. Sentinel `grade=0` for non-school content. Idempotent on `(source_file, section_title)`. |
| Audit script (this brief, ad-hoc) | FTS in-sync check via `SELECT COUNT(*) FROM {base}` vs `SELECT COUNT(*) FROM {fts}` on the 5 known shadow tables. |
| Wiki track aliasing | `ukrainian_wiki.track` = DOMAIN name (figures, works, historiography, periods, …); curriculum tracks read via `TRACK_DOMAINS` in `scripts/wiki/config.py`. Documented as intentional. |

## Open PR carry-over

**PR #1982** (textbook_sections backfill): pytest still pending at handoff;
others (CodeQL, ruff, prompt-lint, schema-drift, gitleaks, radon, frontend,
secret-scan) all green. Advisory `review / review` failed (expected). Merge
when pytest passes:
```bash
gh pr merge 1982 --squash --delete-branch
git worktree remove --force .worktrees/dispatch/claude/section-coverage-2026-05-14
git pull --ff-only origin main
```

## Worktrees on disk at handoff

```
$ git worktree list
main + 5 stale build worktrees (a1-my-morning-*) + 3 stale dispatch worktrees +
.worktrees/dispatch/claude/section-coverage-2026-05-14 (← PR #1982)
```

The build worktrees and old dispatch worktrees are stale (branches merged or
abandoned). Safe to clean any time; not blocking.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs".
MD-only per #M-2 ai→ai. Companion canonical configs: PR #1982 adds
`scripts/ingest/_section_coverage.py` as the shared lesson-section helper.*
