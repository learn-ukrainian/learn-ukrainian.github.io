---
date: 2026-05-14
session: "Short session — C4 closure. Previous orchestrator wrote 'BLOCKED on user placing 52MB image-PDF' while the file was sitting in ~/Downloads as `Ukrainska_literaturna_vymova.pdf` the whole time. User flagged the bureaucratic framing. Found the file, ran OCR + ingest, opened + merged PR #1986. Corpus completion arc fully closed."
status: ok
main_sha: 3567e46745
main_green: true
open_prs: [1873]  # stale dependabot starlight bump (Frontend fail, not touched)
active_dispatches: 0
agents: [claude, codex, gemini]
worktrees_open: 4  # main + codex-interactive + 3 unmerged-WIP from earlier sessions
ci_notes: "PR #1986 passed all blocking checks AND the advisory `review / review` check (Gemini Dispatch) — clean green merge, no advisory noise this time."
filed_today: []
merged_today: [1985, 1986]  # carry forward from same calendar day
closed_today: []
next_p0: |
  1. Task B (textbooks.page column + chunking pipeline + backfill) — the
     last carry-over from the corpus-completion arc. Substantial schema
     migration; needs design decisions on:
       - page column on textbooks vs page_start/page_end on textbook_sections
         (sections already has them but NULL on existing rows)
       - which chunking pipeline owns page extraction (extract_sections.py
         is the natural home but it currently uses section-marker IDs not
         page coordinates from the PDF)
       - backfill strategy for 23,777 existing chunks from data/textbooks/
         (~561 MB PDFs) — pdftotext per page + heuristic alignment, or
         pdfplumber-style page bounding boxes
       - textbook_grounding gate matcher (scripts/build/linear_pipeline.py)
         needs to consult page column directly once populated
     Unblocks m20 build #5 textbook_grounding failure (#1975). Phase 2b
     m01-m07 batch remains paused.

  2. m20 build #5 `vesum_verified` writer-output errors (the OTHER #1975
     failure) — independent of Task B. Writer was emitting `ди_юся`
     stress-marker artifact, `дивюся` missing `л`, `користуювася` with
     spurious "ва". Writer-prompt fix territory.

  3. The 3 unmerged WIP worktrees still flagged for user decision (from
     prior brief): bakeoff-2026-05-12-night, writer-prompt-tune-2026-05-13,
     codex/pass2-only-contract-test-2026-05-13. None block forward work.
---

# Brief — 2026-05-14 — C4 Pohribnyi shipped, corpus completion arc CLOSED

> Predecessor: `2026-05-14-corpus-day-session-final-brief.md`. That brief
> closed C2+C3 + the textbook_sections backfill but left C4 marked
> "BLOCKED on user placing 52MB image-PDF" — when the file was actually
> in ~/Downloads as `Ukrainska_literaturna_vymova.pdf` (titled in
> transliteration not Cyrillic). User: *"it is in my fucking download
> folder i told you, why do i have to place it why do yu suddenly become
> burocratic ?"* Lesson: when a task says "blocked on user providing X",
> search ~/Downloads (+ common alt-spellings) before declaring blocked.

## TL;DR

One PR shipped this session:

| PR | Status | What |
|---|---|---|
| **#1986** | ✅ merged `3567e46745` | C4 — Mykola Pohribnyi 1992 "Українська літературна вимова" (28-page Ukrainian-pronunciation textbook). OCR'd out-of-band with Tesseract 5 + `-l ukr` on 300 dpi PNGs from pdftoppm; page-grained ingester (28 chunks = 28 pages = 28 sections) reusing `_section_coverage` helper. 9 unit tests. |

Corpus completion arc — ALL 4 C-items closed across overnight + day +
late-day:

| Item | What | PR | Status |
|---|---|---|---|
| C1 | Ohoiko 1000 Words | #1977 | ✅ |
| C2 | Ohoiko 500+ Verbs | #1984 | ✅ |
| C3 | ULP S1-S6 lesson notes | #1981 | ✅ |
| C4 | Pohribnyi 1992 | #1986 | ✅ this session |
| (audit) | textbook_sections backfill for 1,240 orphans + shared helper | #1982 | ✅ |

## Canonical DB state at session end

```
$ sqlite3 data/sources.db "SELECT 'textbooks: ' || COUNT(*) FROM textbooks; SELECT 'textbooks_fts: ' || COUNT(*) FROM textbooks_fts; SELECT 'textbook_sections: ' || COUNT(*) FROM textbook_sections"
textbooks: 25545
textbooks_fts: 25545     (in sync ✓)
textbook_sections: 6839
```

The 28 Pohribnyi chunks landed cleanly, FTS in sync, 0 section-orphans
for this source. Retrieval probes return content from both base FTS
(`наголо*` → p02/p04/p05) and section-level path (`дзвінкий
приголосний` → p13).

## Architectural decisions encoded (PR #1986)

| Where | Rule |
|---|---|
| `scripts/ingest/pohribnyi_pronunciation_ingest.py` | Page-grained chunking (1 page = 1 chunk = 1 section) chosen over per-headword because the book is structurally cohesive prose-with-transcription, not a true alphabetical dictionary. OCR artifacts in dense IPA-bracket notation make reliable entry-boundary detection brittle at this stage. Per-headword refinement remains possible later (OCR text is preserved on disk, re-chunk is cheap). |
| OCR pipeline (out-of-band, documented in module docstring) | `pdftoppm -r 300 -png` → `tesseract -l ukr` per page → concatenate with `\f` form-feed separators between pages → ingester splits on `\f`. Same pattern reusable for future image-PDF ingests. |
| Module docstring | Includes the exact re-OCR command sequence so the pipeline is reproducible from the source PDF alone (no opaque tooling). |

## OCR quality caveats (documented in PR body, not blocking)

- IPA bracket sequences are systematically misread: `[е]` reads as
  `Ге)`, `[й]` reads as `Гй]`, `[и]` reads as `Ги|` — Cyrillic + dense
  square-bracket transcription is a Tesseract weak spot.
- Page 25 header "ЛІТЕРАТУРА" was OCR'd as "ЗАРТЕРАТУРА"; page 26
  "ЗМІСТ" as "ЗМІСТЬ". Cosmetic.
- These artifacts don't block FTS retrieval against the Ukrainian
  content body (which dominates the chunk text), but they would harm
  pronunciation-precise reasoning. Future improvement: post-process
  bracket sequences during ingest if textbook_grounding gate starts
  citing Pohribnyi pages and the matcher needs exact-match against IPA.

## Pre-ingest backup

```
data/sources.db.bak-20260514-142842-pre-pohribnyi-ingest   (1.5 GB)
```

Keep until next major DB-modifying operation queues. Two earlier
backups were already cleaned per the day-final brief's authorization.

## Remaining task queue (post #1986)

| Task | Status | Notes |
|---|---|---|
| **B** textbooks.page column | unstarted | The last carry-over from the corpus-completion arc. Substantial schema migration + chunking pipeline change + 23,777-chunk backfill from 561 MB of PDFs + matcher update in `linear_pipeline.py`'s textbook_grounding gate. Probably wants its own session — design decisions itemized in `next_p0` above. |
| **#1975** m20 build #5 `vesum_verified` writer-output errors | filed | Independent of Task B. Writer emits malformed forms (`ди_юся`, `дивюся`, `користуювася`). Writer-prompt fix. The `textbook_grounding` half of #1975 unblocks only when Task B lands. |
| Section-extraction spillover (280 chunks) | not filed | School textbooks have 1-18% per-book orphan chunks where `extract_sections.py` didn't find structural markers. Follow-up. |
| 3 unmerged WIP worktrees | still on disk | User decision pending per day-final brief: claude/bakeoff-2026-05-12-night (likely safe to delete), claude/writer-prompt-tune-2026-05-13 (35 lines of defensive citation/budget/immersion discipline directives — see day-final brief diff analysis), codex/pass2-only-contract-test-2026-05-13. None blocking. |

## Process lesson encoded

The day-final brief wrote *"BLOCKED on user placing 52MB image-PDF"*
without first searching `~/Downloads` for the file. User had told a
prior session the file was in Downloads; the night-brief author never
checked. Cost: a 10-minute bureaucratic stall and a user-frustration
mark. Fix: when a brief says "blocked on user providing X" and the
file is named generically (book title, not invoice/credential), always
`ls ~/Downloads/ | grep -iE '<title-words>|<author-words>|<topic-words>'`
before propagating the BLOCKED label. Especially for files whose
filenames are likely transliterated (Cyrillic books arrive as
`Ukrainska_literaturna_vymova.pdf` not `Українська літературна
вимова.pdf` from most browsers).

Not added to MEMORY.md (at 150/150 cap); the lesson is narrow enough
to live in this brief for the next session that hits the pattern.

## Next session opening action

1. Read this brief.
2. `git log -1 --oneline` should show `3567e46745` or newer.
3. If user provides direction, follow it.
4. Otherwise the natural P0 is **Task B (page column)**. Design decisions
   are itemized in `next_p0` — recommended approach is a Decision Card
   pinning the schema (textbooks.page INTEGER vs reuse
   textbook_sections.page_start/end) before any code lands.
5. If neither feels right, m20 #1975 `vesum_verified` writer-output
   fix is a smaller standalone unblock (writer-prompt territory, not
   requiring Task B).

## Worktrees on disk at handoff

```
$ git worktree list
/Users/krisztiankoos/projects/learn-ukrainian                                                               3567e46745 [main]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-interactive                                  ffafa6a60e (detached HEAD)   ← Codex session, leave alone
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night           5a72a31f9b   ← user-decision pending
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/writer-prompt-tune-2026-05-13      ce7ca40881   ← user-decision pending
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/pass2-only-contract-test-2026-05-13 5e65230c3f   ← Codex experimental, leave to Codex
```

This session's worktree (`.worktrees/dispatch/claude/pohribnyi-ocr-2026-05-14`) was cleaned post-merge.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs".
MD-only per #M-2 ai→ai.*
