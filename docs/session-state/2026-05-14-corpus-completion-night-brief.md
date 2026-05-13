---
date: 2026-05-14
session: "Overnight autonomous corpus-completion session. User pivoted away from m20 build-iteration arc (#1969 fix merged but build #5 still red on different gates) to corpus expansion priority — Anna Ohoiko + ULP + Pohribnyi book ingestion. Discovered systemic data-loss in 2026-05-13 Pohribnyi YT dispatch (#1973) — Codex's success summary was hallucinated, canonical sources.db received zero rows for 9h. Also found systemic textbook indexing gap: chunks are sectioned (_sNNNN), curriculum plans cite pages, no page column exists."
status: ok
main_sha: 9c54ad8029
main_green: true
open_prs: [1978]
active_dispatches: 0
agents: [claude, codex, gemini]
worktrees_open: 5  # main + 1 task-D PR + 3 build worktrees from yesterday's m20 iterations + 1 build worktree from session-start
ci_notes: "All session PRs (#1976, #1977, #1978) pass blocking checks. Advisory `review / review` (Gemini Dispatch) fails on each — non-blocking per #M-0.5. PR #1977 pytest took ~55 min from PR-creation to completion (only 4.5 min runtime — long queue delay)."
filed_today: [1975]
merged_today: [1974, 1976, 1977]
closed_today: [1969]  # closed by #1974
next_p0: |
  Complete the inline corpus ingestion sequence the user started 2026-05-14:
    C2: Anna Ohoiko 500+ Verbs (parser DESIGN PENDING — different shape than 1000-words)
    C3: ULP 1-00 → 6-00 Lesson Notes (six prose books, sequential)
    C4: Pohribnyi book PDF (OCR pipeline required first — Tesseract uk)
  Plus carried structural fixes:
    B: textbooks.page column + PDF backfill (~150-300 LOC + re-ingest cycle)
    1975: m20 build #5 textbook_grounding + vesum_verified gate diagnoses

  After C2-C4 land, re-run m20 build #6 if user wants — but Phase 2b
  m01-m07 batch is still paused per user pivot. m20 itself has 2
  remaining gate failures (vesum_verified writer-output errors,
  textbook_grounding page-matcher gap — both filed at #1975).
---

# Brief — 2026-05-14 overnight — corpus completion (Ohoiko ingest started, page-index gap surfaced)

> Predecessor: `2026-05-13-late-routing-economics-corpus-expansion-brief.md`. This session pivoted hard from m20 module building to corpus completion after the user identified a corpus data-loss incident and structural indexing concerns.

## TL;DR

Three PRs shipped overnight, all merged or in-flight:

| PR | Status | What |
|---|---|---|
| **#1976** | ✅ merged `7f1057b4de` | Fix `external_articles.channel_id` empty on all 1199 historical rows + populate audio metadata (`speaker`, `video_id`, `duration_s`). Migration UPDATEd 1199 rows + INSERTed 6 Pohribnyi rows inline. |
| **#1977** | ✅ merged `9c54ad8029` | New ingester `scripts/ingest/ohoiko_books_ingest.py`. Anna Ohoiko *"1000 Most Useful Ukrainian Words"* 2nd ed → 1000 entries indexed in textbooks table (source_file=`anna-ohoiko-1000-words-2nd-ed`). 15 unit tests. |
| **#1978** | 🟡 open | Docs rule: ingest briefs now MUST quote BEFORE/AFTER/SAMPLE sqlite output. Failure-record entry for the 2026-05-13 Pohribnyi loss. |

Critical findings:
1. **Pohribnyi YT data was never in canonical sources.db.** PR #1973's success summary was hallucinated — JSONL file didn't exist on disk, all 1199 external_articles rows had `channel_id=''`. Re-fetched + re-ingested inline.
2. **All textbook chunks use section-IDs (`_sNNNN`), not page numbers.** Plans cite `p.187` but corpus has `_s0187` (section 187). textbook_grounding gate failure on m20 #5 is symptomatic of this gap. No `page` column exists.
3. **Codex/Gemini dispatch trust gap.** The 2026-05-13 Pohribnyi failure exposed the missing guardrail: no quoted DB-state evidence in PR bodies. Closed by #1978.

## DB state at session end

Verified deterministic — actually-canonical `data/sources.db`:

```
$ sqlite3 data/sources.db "SELECT channel_id, COUNT(*) FROM external_articles GROUP BY channel_id ORDER BY 2 DESC"
ulp_youtube|316
imtgsh|203
realna_istoria|176
ulp_blogs|164
istoria_movy|158
komik_istoryk|107
other_blogs|75
pohribnyi_pronunciation|6

$ sqlite3 data/sources.db "SELECT source_file, COUNT(*) FROM textbooks WHERE source_file LIKE 'anna-ohoiko%' GROUP BY source_file"
anna-ohoiko-1000-words-2nd-ed|1000
```

External articles: 1199 → 1205 (+6 Pohribnyi).
Textbooks: 23,777 → 24,777 (+1000 Ohoiko words).
FTS5 row count matches base table (verified `textbooks_fts COUNT = 24777`).

## Architectural findings

### 1. Pohribnyi #1973 data-loss postmortem

Codex result-file summary 2026-05-13: *"Ingestion fetched 6 videos into data/external_articles/pohribnyi_pronunciation.jsonl. DB migration inserted 35 chunks for channel_id='pohribnyi_pronunciation' and moved external rows 1205 -> 6511."* All three claims (JSONL on disk, 35 DB chunks, row-range shift) were false in canonical state. Codex stdout AND stderr logs were 0 bytes for 22 min of work — no execution trace.

Most likely root cause: transaction not committed OR migration ran on Codex's worktree-local DB (was the symlink actually set up? `delegate.py:_provision_data_symlinks` does it, but logs prove nothing about whether the symlink target succeeded for that run).

Failure record + new evidence requirements encoded in #1978.

### 2. Textbook page-vs-section index gap

```
$ sqlite3 data/sources.db "SELECT chunk_id FROM textbooks WHERE source_file='10-klas-ukrmova-karaman-2018' LIMIT 5"
10-klas-ukrmova-karaman-2018_s0000
10-klas-ukrmova-karaman-2018_s0001
10-klas-ukrmova-karaman-2018_s0002
10-klas-ukrmova-karaman-2018_s0003
10-klas-ukrmova-karaman-2018_s0004
```

All 23,777 textbook chunks have `_sNNNN` (section N) IDs. Schema has `parent_section_id` (textbook_sections FK) but no `page` column. The textbook_grounding gate on m20 #5 failed looking for `p.187` (corpus has `_s0187`, which IS section 187, NOT page 187 — they coincide rarely).

**Fix scope (Task B, unstarted):**
- ALTER TABLE textbooks ADD COLUMN page INTEGER
- Modify chunking pipeline (likely `scripts/wiki/extract_sections.py` or similar) to extract page numbers during PDF→chunk extraction
- Backfill 23,777 existing chunks from `data/textbooks/*.pdf` (561MB)
- Update textbook_grounding matcher to query `page` column directly

Substantial work, separate session. Filed as Task #2.

### 3. m20 build #5 outcome (issue #1975)

Build #5 fired at session start to verify the #1969 pre-emit-checklist fix. Result: 2 of 21 gates fail:

- `vesum_verified`: writer emitted malformed forms (`ди_юся` stress-marker artifact, `дивюся` missing л, `користуювася` spurious "ва"). Real writer-correctness bugs.
- `textbook_grounding`: matcher can't resolve `Караман Grade 10, p.187` because chunks are sectioned not paged (per finding 2 above).

The pre-emit checklist #1974 DID fix `resources_search_attempted` (writer made multimedia search calls). Issue #1975 has the full gate dump + reproducer queries.

m20 GREEN is gated on Task B (page column fix). Phase 2b m01-m07 batch remains paused.

## Decisions encoded

| Where | Rule |
|---|---|
| `docs/best-practices/deterministic-over-hallucination.md` (PR #1978) | Every DB-write dispatch brief MUST require BEFORE/AFTER/SAMPLE quoted sqlite output in the PR body. Orchestrator independently re-verifies against canonical DB before merging. |
| `scripts/wiki/build_sources_db.py` (PR #1976) | `_ingest_external_articles()` always derives `channel_id` from JSONL filename stem (canonical); per-record `channel_id` field in JSONLs is informational only. Avoids hyphen/underscore drift between ingest runs. |
| `scripts/ingest/ohoiko_books_ingest.py` (PR #1977) | Ohoiko books use a `BOOKS` registry pattern. Parser gates: Cyrillic-headword filter + max_entry_number cap + monotonicity guard + section terminators. Idempotent on re-run; `--force` to overwrite. |

## Open PR carry-over

**PR #1978** (Task D — docs/determinism rule update): 5 CI checks pending at handoff time. Wait for green, then merge with `gh pr merge 1978 --squash --delete-branch`. No code changes; pytest impact zero. Advisory `review/review` fail expected (Gemini Dispatch noise).

After merge:
```bash
git worktree remove --force /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/db-write-evidence-rule-2026-05-14
git branch -d inline/db-write-evidence-rule-2026-05-14
```

## Remaining task queue (priority order, post-#1978)

| Task | Status | Notes |
|---|---|---|
| **C2** Ohoiko 500+ Verbs | unstarted | Different parser shape than 1000-words. Use `№ NNN` markers (numero symbol, U+2116, preceded by `\x0c` form-feed page-break) to bound each verb page. ~500 entries from `№ 1` to `№ 500+`. Skip the grammar-guide intro (lines 1-3115ish) and the indexes at end. Each verb page has full conjugation tables + examples. Estimate: ~150 LOC parser + ~10 LOC BOOKS registry entry + tests. Source: `docs/references/private/500+ Ukrainian Verbs - Ukrainian Lessons - PDF.txt` (32K lines, 3MB). Schema: same `textbooks` table, `source_file='anna-ohoiko-500-verbs'`. |
| **C3** ULP 1-00 → 6-00 | unstarted | 6 prose books, ~9MB total (576K → 2.3MB ascending). Write a separate prose-chunk parser (not entry-based; paragraph-aware or section-aware). One book per ingest run. Source files in `docs/references/private/ULP N-00 Lesson Notes...txt`. Schema: textbooks table, `source_file='ulp-N-00-lesson-notes'`, `author='Ukrainian Lessons Podcast'`. |
| **C4** Pohribnyi book | unstarted | 52MB image-based PDF, 28 pages (CorelDRAW 2010). `pdftotext` returns nothing — needs OCR. Pipeline: Tesseract with `-l ukr` lang model. Verify Tesseract is installed (`tesseract --version`) before starting. Once text extracted, ingest into textbooks table. |
| **B** textbooks.page column | unstarted | Big task — schema migration + chunking pipeline change + full backfill from PDFs. Unblocks textbook_grounding gate (m20 #1975). Probably wants its own session. |
| **#1975** m20 build #5 gate failures | filed | Diagnosis exists in the issue body. `vesum_verified` needs writer-side fixes (malformed forms); `textbook_grounding` unblocked by Task B. Phase 2b m01-m07 batch stays paused until m20 is GREEN. |

## Next session opening action

1. Read this brief.
2. Confirm main is current: `git log -1 --oneline` should show `9c54ad8029` or newer.
3. Check + merge PR #1978 if CI is green (or has only advisory `review/review` failure):
   ```
   gh pr checks 1978
   gh pr merge 1978 --squash --delete-branch
   git worktree remove --force /Users/.../db-write-evidence-rule-2026-05-14
   git branch -d inline/db-write-evidence-rule-2026-05-14
   ```
4. Resume corpus ingestion sequence. Recommended: C3 (ULP) before C2 (verbs) — ULP prose chunks are mechanically simpler than verb-page parsing. User originally asked for C2 first ("smallest first") but C2's structural complexity changes that — flag the deviation when reporting.
5. C4 (Pohribnyi book OCR) can run in parallel with C3 if `tesseract` is installed locally.
6. Task B (page column) is a separate session — large scope, needs design decisions.

## Inline-orchestrator pattern (USER-DIRECTED 2026-05-14)

User established this pattern after the Pohribnyi loss: *"I run all ingestion inline as orchestrator"*. Routing for THIS session's ingestion work was NOT Gemini-lane per #M0; the orchestrator runs all ingests directly against canonical `data/sources.db`, captures BEFORE/AFTER/SAMPLE evidence, then commits the SCRIPT + tests via worktree. DB state is data-only (gitignored), so PR review focuses on the ingester's correctness; the migration evidence lives in the PR body.

Continue this pattern for C2-C4 unless the user reverts the direction.

## Worktrees on disk at handoff

```
$ git worktree list
/Users/krisztiankoos/projects/learn-ukrainian                                                                main
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260513-122043                build/a1/my-morning-20260513-122043
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260513-161726                build/a1/my-morning-20260513-161726
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260513-164953                build/a1/my-morning-20260513-164953
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260513-193448                build/a1/my-morning-20260513-193448
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/builds/a1-my-morning-20260513-221945                build/a1/my-morning-20260513-221945
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-interactive                                   (detached)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/bakeoff-2026-05-12-night            claude/bakeoff-2026-05-12-night
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/db-write-evidence-rule-2026-05-14   inline/db-write-evidence-rule-2026-05-14  (← PR #1978)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/writer-prompt-tune-2026-05-13       claude/writer-prompt-tune-2026-05-13
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1476-auto-path                       codex/1476-auto-path-2026-04-26
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/pass2-only-contract-test-2026-05-13  codex/pass2-only-contract-test-2026-05-13
```

The 5 m20 build worktrees can be cleaned after Task B lands and m20 build #6 verifies the page-index fix. The codex/claude dispatch worktrees from before May 12-13 are stale (their branches are merged or abandoned) — safe to clean any time but not blocking.

## Pre-commit backup

Pre-channel-id-fix sources.db backup (1.5GB, untracked):
`data/sources.db.bak-20260513-224311-pre-channel-id-fix`

Keep until Task B completes — that's another major DB-modifying operation that warrants a fresh backup of its own.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". MD-only per #M-2 ai→ai. Companion canonical configs: none new this session. Failure record: `docs/best-practices/deterministic-over-hallucination.md` (added in PR #1978).*
