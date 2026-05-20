# Dispatch Brief — ESUM OCR Closeout (Codex)

**Date:** 2026-05-19
**Issue:** [#2001](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2001) — Re-OCR all 6 ESUM volumes
**Prerequisite:** vol5 + vol6 OCR complete on main project (status: `data/raw/esum/gemini-ocr/vol5/` ≥ 695/705 + `vol6/` ≥ 559/569 — straggler tolerance ~10 pages/vol).
**Target agent:** Codex (script changes + multi-step orchestration + regex work — its lane).
**Mode:** danger. **Worktree:** mandatory.

## Critical context — what we discovered during OCR

The Gemini-2.5-flash bulk OCR has a previously-undetected failure mode: **the model occasionally goes into a repetition loop**, emitting valid-looking Ukrainian dictionary entries 5-60 times each. Filter v2 (`bulk_ocr_gemini.py:is_low_quality_output`, hardened by PRs #2115 + #2129) does NOT catch this shape because the repetitions are individually well-formed dictionary lines.

**Confirmed bad pages as of 2026-05-19 16:45 local:** 29 across vol3 (9) + vol4 (13) + vol5 (7). vol1 + vol2 are clean. Population will grow during the remaining OCR.

**Diagnostic signature (deterministic):** unique-line ratio < 0.20 over a file with ≥ 100 lines. Normal pages run 0.25-0.40. Worst observed: `vol3/p0088` = 2,418 lines, **1% unique**.

Reproduce the scan with:

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python - <<'PY'
from pathlib import Path
for md in sorted(Path("data/raw/esum/gemini-ocr").glob("vol*/p*.md")):
    if "quarantine" in str(md): continue
    lines = md.read_text().splitlines()
    if len(lines) < 100: continue
    ratio = len(set(lines)) / len(lines)
    if ratio < 0.20:
        print(f"{md}  lines={len(lines)} unique={len(set(lines))} ratio={ratio:.2f}")
PY
```

## Job

Land a SINGLE PR closing #2001 that does the closeout in this exact order:

### A. Harden `is_low_quality_output` filter

Edit `scripts/etymology/bulk_ocr_gemini.py`:

- Add a `repetition_ratio` check: for outputs with ≥ 100 lines, if `len(set(non_empty_lines)) / len(non_empty_lines) < 0.20`, return `True` (low quality).
- Strip empty lines from both numerator and denominator (normal pages have ~30% empties from formatting; the threshold above is calibrated for non-empty count).
- Existing refusal + completion-meta + repetition substring checks stay; this is an additional gate, not a replacement.

Tests in `tests/etymology/test_bulk_ocr_quality.py`:

- Positive: feed the 29 known-bad files (paths above) one at a time; each must return `True`.
- Negative: feed 10 known-good vol5 pages from p0231, p0234, p0246, p0259, p0286, p0289, p0290, p0231, p0237, p0240; each must return `False`.
- Edge: a 50-line file with 5 unique lines (ratio 0.10) — should NOT trigger because below the 100-line floor.
- Edge: a 100-line file with 25 unique lines (ratio 0.25) — should NOT trigger (above threshold).
- Edge: a 100-line file with 15 unique lines (ratio 0.15) — should trigger.

Run `.venv/bin/pytest tests/etymology/test_bulk_ocr_quality.py -v` until green. Per #M-7: pytest is mandatory before any push touching this file.

### B. Quarantine all flagged pages (full sweep with hardened filter)

Sweep ALL of `data/raw/esum/gemini-ocr/vol{1..6}/*.md` against the new filter:

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
mkdir -p data/raw/esum/gemini-ocr/_quarantine/2026-05-19-repetition-hallucination
.venv/bin/python - <<'PY'
import sys; sys.path.insert(0, 'scripts/etymology')
from bulk_ocr_gemini import is_low_quality_output
from pathlib import Path, PurePath
import shutil
quar = Path("data/raw/esum/gemini-ocr/_quarantine/2026-05-19-repetition-hallucination")
quar.mkdir(parents=True, exist_ok=True)
moved = []
for md in sorted(Path("data/raw/esum/gemini-ocr").glob("vol*/p*.md")):
    if "_quarantine" in str(md): continue
    if is_low_quality_output(md.read_text()):
        dst = quar / f"{md.parent.name}_{md.name}"
        shutil.move(str(md), str(dst))
        moved.append(str(md))
print(f"quarantined: {len(moved)}")
for m in moved: print(" ", m)
PY
```

Capture the output count + paths into the PR body.

### C. Re-OCR quarantined pages under fresh tenant

**User will rotate Gemini OAuth before this step fires.** Coordinate via orchestrator.

After rotation, refire `bulk_ocr_gemini.py` exactly as in the handoff (`--concurrency 1 --rpm 8 --model gemini-2.5-flash`). The script is idempotent and will pick up the now-missing pages. Run until QUOTA_HALT or completion.

Expected outcome: ~30-50 pages re-OCR'd, most clearing on the new tenant (handoff history: vol3 stragglers cleared, vol2 stragglers cleared). Any that still fail with hardened-filter rejection enter a SECOND quarantine round; user input required at that point.

### D-J. Standard closeout (handoff lines 111-125)

After C completes with all vols at ≥ 99% (allow ~5-10 hard-failure stragglers per vol, document in PR body):

- **D. Concat:** For each vol N, write `data/raw/esum/vol{N}.txt` (overwrite legacy) by concatenating `data/raw/esum/gemini-ocr/vol{N}/p*.md` in page order. Use the existing `concatenate_completed_volumes()` helper if it works, or write inline; the legacy `vol{N}.txt` files in git are what we're replacing.
- **E. Re-ingest:** `.venv/bin/python scripts/ingest/esum_ingest.py --input data/raw/esum/vol{N}.txt --output data/processed/esum_vol{N}.jsonl --vol N` for each vol. (The `--source-suffix gemini --replace` flags in the handoff are aspirational — current script signature uses positional in/out/vol. If you want to add the flags, do it cleanly; otherwise just loop.)
- **F. Regex tighten:** `scripts/etymology/extract_cognate_forms.py` — add digit filters + Ukrainian function-word filters. Test against the new JSONL — false-positive rate on a 100-entry sample must drop noticeably (capture before/after counts in PR).
- **G. Manifest rebuild:** `starlight/src/data/etymology-manifest.json` — regenerate from the new corpus.
- **H. Glosses cleanup:** `starlight/src/pages/etymology/index.astro` — strip fabricated featured-card glosses (the Phase 1 hand-written ones that no longer match).
- **I. Spot-check:** 20-entry deterministic-random sample with **`seed=2001`** (handoff requirement). Use `random.Random(2001).sample(entries, 20)`. Manually verify each against the source vol{N}.txt; report verdict in PR body.
- **J. PR:** Single PR titled `feat(etymology): close #2001 — Gemini OCR corpus + filter hardening + closeout`. Body must include section "What this PR does" and "Verifiable claims" per the verifiable-claims preamble below.

## Verifiable claims preamble (per #M-4)

| Claim | Tool | Evidence in PR body |
|---|---|---|
| Filter catches the 29 known-bad pages | `pytest tests/etymology/test_bulk_ocr_quality.py -k positive -v` | raw `passed` line |
| All clean pages still pass | `pytest tests/etymology/test_bulk_ocr_quality.py -k negative -v` | raw `passed` line |
| Quarantine sweep count | python script in step B | raw count + path list |
| Re-OCR coverage | per-vol final page count `find ... -name "p*.md" \| wc -l` for each vol | numeric, ≥ 99% each |
| Concat output exists | `ls -lh data/raw/esum/vol{1..6}.txt` | 6 lines of raw `ls` |
| JSONL re-ingested | `wc -l data/processed/esum_vol{1..6}.jsonl` | 6 numeric lines |
| Regex tightening effect | before/after false-positive count on a fixed sample | numeric delta |
| Spot-check (seed=2001) verdict | manual verification table in PR body | 20 entries, accept/reject per entry + reasoning |
| Ruff clean | `.venv/bin/ruff check scripts/etymology/ scripts/ingest/` | raw `All checks passed!` |
| Pytest clean | `.venv/bin/pytest tests/etymology/ tests/ingest/` | raw `N passed` summary |
| PR opened | `gh pr view --json url` | raw URL |

## Halt / escalate triggers

| Trigger | Action |
|---|---|
| Re-OCR quarantine round 2 still has > 20 hard failures | Halt, write status to orchestrator. Bad-scans hypothesis becomes viable; may need image preprocessing pass. |
| Spot-check (step I) finds > 2 of 20 entries semantically wrong | Halt before PR. Filter or ingestion bug. |
| Concat produces a vol{N}.txt smaller than the legacy vol{N}.txt by > 10% | Halt. Either content was lost or legacy had filler we no longer have. Investigate before continuing. |

## Branch + commit conventions

- Branch: `feat/etymology-closeout-2001`
- Conventional commits per step (filter-harden, quarantine-sweep, re-OCR, concat, ingest, regex, manifest, glosses, spotcheck)
- X-Agent trailer per AGENTS.md

## Backups (already done — DO NOT REDO)

Per-page `.md` source tree was tarballed + pushed to `~/My Drive/learn-ukrainian-backups/esum-ocr-snapshot-2026-05-19.tar.gz` (18 MB, SHA256 verified) on 2026-05-19. If you need to recover, restore via that. Companion manifest alongside.
