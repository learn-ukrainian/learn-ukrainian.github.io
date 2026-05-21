# Issue #2001 ESUM re-OCR — orchestrator handoff (2026-05-21)

> **Scope:** OCR project (issue #2001) only. Continuation of `docs/session-state/2026-05-20-issue-2001-ocr-handoff.md`.
> Does **not** touch the main session handoff or `current.md`.

## TL;DR — direction changed

**The Gemini-2.5-flash re-OCR project is DEAD.** Bake-off (Codex `esum-bakeoff-2026-05-21`) + independent spot-check found 97% wrong-page hallucination rate: Gemini was producing clean-looking Ukrainian etymology text for ENTIRELY DIFFERENT pages from the scan it was given (e.g., page of РАЙ-words → output of М-words). 3,179 generated files are corpus garbage.

**Internet Archive has clean text layers for all 6 volumes already** — we discovered this mid-session. Two viable paths:
- **`_text.pdf`** (all 6 vols): searchable PDF, extract via `pdftotext`. 95%+ token agreement with ABBYY.
- **`_abbyy.gz`** (vols 1, 2, 3, 6 only): ABBYY FineReader XML — gold-standard dictionary OCR with structured layout.

Plan locked: **ABBYY XML for vols 1/2/3/6, text.pdf for vols 4/5**, parsers adapted per source format, sources.db reloaded.

## Immediate next action

**WORK GOES IN GIT WORKTREES from here on.** Three GitHub issues filed (see §6) to drive parser adaptation. Pick the highest-priority issue, `git worktree add`, dispatch or implement.

Do NOT refire `bulk_ocr_gemini.py`. The script is preserved for future visual-OCR experiments but the current data path is dead-ended.

## What this session (2026-05-20 morning → 2026-05-21 mid-day) accomplished

### A. OCR script kept running through the morning
- Refired post-OAuth-rotation at 20:27 local 2026-05-20
- Made it 8.5h to BULK_QUALITY_HALT at vol6/p0113 (32 errors / 100-page rolling window)
- Net added 134 net pages before halt (cumulative 3,133 / 3,691 = 84.9%)
- 17 hallucinated files quarantined throughout the run:
  - 10 originally caught by `shadow uniqueness` check (≥100 lines, ratio < 0.20)
  - 6 added by new `substring-repetition` check (single-line files shadow check skipped)
  - 1 added by ESUM-MCP fact-check (semantic hallucination — `vol5/p0469` "сму́шок" cited fake cognates)
- Quarantine dir preserved at `data/raw/esum/gemini-ocr/_quarantine/2026-05-19-repetition-hallucination/` (gitignored, kept locally)

### B. PR #2171 (Policy Engine fix) shipped
- Replaced deprecated `--allowed-tools` (silent no-op in gemini-cli 0.42.0) with `--policy <toml>`
- Eliminated `Error executing tool web_fetch` failures
- Codex dispatch authored, all blocking CI green, merged 08:39 local

### C. Bake-off (`esum-bakeoff-2026-05-21`) ran the 4-pipeline quality comparison
- 30 random pages × 4 pipelines (Tesseract / Gemini-2.5 / Gemini-3.5/agy / pdf-text-layer)
- REPORT at `audit/etymology-ocr-bakeoff/REPORT.md` on branch `codex/esum-bakeoff-2026-05-21`
- Verdict: **Tesseract 0.74/0.92 vs Gemini-2.5 0.14/0.03 vs agy 0.13(broken)/0.13** — Gemini-2.5 catastrophically bad on semantic_acc (97% wrong-page hallucination)
- agy promising on the 4-of-30 it returned text (0.98/0.98) but blank stdout on 26/30 — headless reliability broken
- pdf-text-layer "not testable in dispatch" because Codex didn't find local PDFs

### D. Independent verification (orchestrator spot-check)
- vol5/p0017 confirmed wrong-page (scan = РАЙ-words; Gemini emitted М-words `м'ясо, мука, муха, місяць, морок`)
- vol3/p0200 confirmed wrong-page (scan = Л-section; Gemini emitted Ж-section `ЖОЛО́Б`)
- vol4/p0500 confirmed wrong-page (scan = П-section полоскати; Gemini emitted К-section `КРА́ПКА`)
- vol1/p0100 suspicious — content overlap but mislabeled entry boundaries
- Pattern: Gemini reads SOMETHING from the image but generates etymologically-plausible content for a different page entirely. Tesseract was on the right page 92% of the time.

### E. Internet Archive discovery — clean text layers available
JP2 zips named `etslukrmov{1..6}_jp2.zip` traced to IA item IDs. Each item has multiple pre-extracted formats:

| Format | Vols available | Purpose |
|---|---|---|
| `_djvu.txt` | all 6 | What we already had in `data/raw/esum/vol{N}.txt` (byte-identical) — the existing deployed source |
| `_text.pdf` | all 6 | Searchable PDF; `pdftotext` extracts clean text layer |
| `_abbyy.gz` | 1, 2, 3, 6 | **ABBYY FineReader XML** — gold-standard dictionary OCR, structured layout |
| `_djvu.xml` | all 6 | DjVu XML with character bounding boxes |
| `_hocr_searchtext.txt.gz` | 4, 5 | hOCR search text (gzipped) |

Cross-validation of text.pdf vs ABBYY on 20 random pages × 4 vols: **mean Jaccard 0.953**, min 0.911, max 0.995 — both pipelines agree on content. Differences are hyphenation handling + a handful of single-char OCR variants.

### F. Cleanup — ~9 GB freed locally + Drive backup removed
- Deleted `data/raw/esum/jp2-staging/` (8.7 GB of JP2 zips + extracted directories — re-downloadable from IA)
- Deleted `data/raw/esum/gemini-ocr/*.md` (121 MB of 3,173 corrupt wrong-page files; preserved `_quarantine/` subdir)
- Deleted `data/raw/esum/vol{1,2,3}-gemini.txt` (35 MB of concatenated wrong-page text)
- Deleted `gemini_ocr_images/` (48 KB temp)
- Deleted Drive backup tarball `~/Library/CloudStorage/.../My Drive/learn-ukrainian-backups/esum-ocr-snapshot-2026-05-19.tar.gz` (18 MB) + manifest

All cleanup files were already gitignored — no tracked file changes from cleanup itself. This session's commit captures only the dispatch briefs + this handoff.

## Current state on disk

### IA source files (all gitignored, persistent in `data/raw/esum/`)
```
data/raw/esum/
├── ia-text-pdf/        # 300 MB — primary source for vols 4, 5
│   ├── vol{1..6}-text.pdf      (24-65 MB each)
│   └── vol{1..6}-text.txt      (extracted via `pdftotext`, no -layout)
├── ia-abbyy-xml/       # 1.9 GB — primary source for vols 1, 2, 3, 6
│   ├── vol{1,2,3,6}-abbyy.gz   (compressed FineReader XML)
│   └── vol{1,2,3,6}-abbyy.xml  (decompressed)
├── vol{1..6}.txt       # 24 MB — existing DjVuTXT (what's deployed; bytewise identical to IA's djvu.txt)
└── gemini-ocr/
    └── _quarantine/    # 17 forensic samples of Gemini hallucination patterns (PRESERVE)
```

### Existing parser
- `scripts/ingest/esum_ingest.py` works on djvutxt format (5,146 entries for vol1)
- Tested on text.pdf plain output: only 1,042 entries parsed (80% loss) — needs adaptation
- Tested on text.pdf -raw output: 1 entry (broken) — even worse
- Reason: parser's entry-boundary heuristics assume djvutxt's specific line-break conventions

### Deployed MCP corpus
- `data/processed/esum_vol{1..6}.jsonl` (29,171 entries total)
- Loaded into `data/sources.db`, served via `mcp__sources__search_esum`
- Known issues visible in spot-checks: wrong-lemma extraction on at least vol4/p0250 (`пагніздь, від, відповідають` for what should be `павун, павутиця, пагін`-family)
- Bake-off scored it 0.74 char_acc / 0.92 semantic_acc — usable, not perfect

## Next workstreams (filed as GitHub issues — work in worktrees)

| Issue | Title | Effort | Depends |
|---|---|---|---|
| **#2174** | [etymology] Adapt esum_ingest.py parser for IA text.pdf format (vols 4, 5) | ~2h Codex | none |
| **#2175** | [etymology] Write ABBYY XML parser for ESUM (vols 1, 2, 3, 6) | ~3h Codex | none |
| **#2176** | [etymology] Reload sources.db from new ESUM JSONLs after parsers ship | 30min inline | #2174 + #2175 |
| **#2177** | [etymology] Preserve 17 Gemini hallucination samples as detection test fixtures | 1h Codex | none |
| **#2178** | [etymology] Close issue #2001 — autopsy + lessons learned | 30min inline | #2174+#2175+#2176 done |

## Sweep loop — no longer needed

The post-Gemini-OCR sweep loop in the 2026-05-20 handoff is RETIRED. There's no more OCR run to monitor. The two scripts that were running:
- `scripts/etymology/bulk_ocr_gemini.py` (PID was 9165, gone) — DO NOT REFIRE
- The shadow uniqueness check — no longer applicable; no new files being produced

## What we learned

### Visual-OCR LLMs hallucinate on dense print at scale
Gemini-2.5-flash produced clean-looking but completely-wrong-page output for ~97% of dictionary pages. The hallucination is invisible from the output text alone (looks like real Ukrainian etymology) and only detectable by comparing against ground-truth. This failure mode is fundamentally worse than classical OCR noise — it silently poisons downstream consumers.

agy (Gemini-3.5-flash) was 0.98/0.98 on the 4-of-30 pages where it returned anything, but blank stdout on 26/30 (broken headless CLI). The model has the capability; the CLI is unreliable. Worth piloting again when agy quota returns IF the blank-stdout bug is fixed AND a semantic-diff gate against Tesseract is added.

### Shadow uniqueness check has a known gap
Today's deeper scan found 6 additional structural hallucinations the shadow check missed because of its `if len(lines) < 100: continue` guard — these were single-line repetition-loops (lemma + comparison series repeated). The fix is a substring-repetition variant. This gap belongs in the closeout brief (Issue #4 — preserve samples + add test fixtures).

### Semantic hallucination is undetectable by automated checks
1-in-6 spot-checked small files (`vol5/p0469` for "сму́шок") had hybrid hallucination: real headword + plausible-looking-but-fake etymology (cited Czech *smutek* "sadness" + Sanskrit *smárati* "remembers" as cognates for "sheepskin"). The shadow check misses this entirely. Detection requires per-page RAG verification against authoritative source. Not currently planned; would need a new workstream if we ever try a visual-OCR pipeline again.

### Internet Archive serves the canonical text layers
The whole project (issue #2001 re-OCR) was solving a problem that was already solved on Internet Archive's side. The publisher's PDFs have text layers, and IA ran ABBYY OCR on JP2 scans, and both are free downloads. We were re-OCRing scans whose owner had already done quality OCR for us. Encoded as lesson: **before launching an OCR pipeline, check the source's existing metadata/text formats on its host**.

## Carry-over from yesterday's handoff (still valid)

- Concurrency rule (#M-9): never run > 1 local OCR at a time — still applies if we ever revive visual OCR
- Build artifacts are load-bearing (#M-10) — the bake-off worktree at `.worktrees/dispatch/codex/esum-bakeoff-2026-05-21/` has irreplaceable per-page evidence files; do NOT remove without committing
- `bulk_ocr_gemini.py` script + `gemini-ocr-policy.toml` preserved on main — useful for future visual-OCR experiments
- `data/raw/esum/gemini-ocr/_quarantine/` preserved with 17 forensic samples

## What this handoff is NOT

- NOT a refire trigger — OCR project is dead, no refire planned or possible without architecture rethink
- NOT updating `docs/session-state/current.md` — separate workstream, main agent owns it
- NOT touching MEMORY.md — cross-session lessons captured here in §"What we learned"; main agent can promote to MEMORY if they choose
- NOT a sweep loop continuation — sweep loop retired
