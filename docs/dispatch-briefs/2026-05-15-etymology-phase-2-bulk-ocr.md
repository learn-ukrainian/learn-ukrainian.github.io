# Dispatch Brief — Etymology Phase 2: bulk Gemini-2.5-Flash OCR

**Date:** 2026-05-15
**Issue:** [#2001](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2001) — Re-OCR all 6 ESUM volumes
**Phase 1 result:** PR #2004 merged 2eb62691d4. Gemini-2.5-Flash matches/beats Pro at 90% exact / 100% plausible cognate recovery on test pages, with **free-tier quota** (Pro is paid/limited).
**Target agent:** **Gemini** (per memory rule M0: routine ingestion + running existing scripts = Gemini's lane, unmetered).
**Effort:** medium.
**Worktree:** mandatory — `.worktrees/dispatch/gemini/etymology-phase-2-bulk-ocr-<stamp>/`.
**Mode:** danger (fire-and-forget; commits + opens PR).

---

## Critical operating constraints

### 1. Model = `gemini-2.5-flash` (NOT Pro)

Phase 1 retest showed Flash 2.5 ≥ Pro on this task: 27/30 exact (90%) vs Pro's 26/30 (87%), both at 100% plausible. Flash is faster, free-tier, and what we're testing the rotation strategy with.

### 2. Daily quota wall — 1,500 requests per account-day

Free-tier 2.5-flash limits: **15 RPM, 1,500 RPD**. Phase 2 has ~4,200 pages → cannot fit in one account-day. **Halt cleanly on quota exhaustion** and emit a `QUOTA_HALT` event so the orchestrator can notify the user to rotate the Gemini account, then re-run. The script MUST be idempotent (skip pages whose output file already exists) so rotation = swap auth, re-run same command.

### 3. PNG path / .gitignore handling

Gemini CLI's `@path` image-input goes through the `read_file` tool, which respects project `.gitignore` by default. Our raw scans MUST be gitignored (~2 GB local) but Gemini still needs to read them.

**Fix:** add to the worktree's `.gemini/settings.json`:

```json
{
  "fileFiltering": {
    "respectGitIgnore": false
  }
}
```

This is project-local — does NOT affect the project root .gitignore or global gemini settings. Git still ignores the binaries; Gemini CLI sees them.

### 4. Backup is via `scripts/backup-data.sh` (rsync → Google Drive)

The user runs `scripts/backup-data.sh` periodically; it catches everything under `data/` regardless of gitignore. So even though raw JP2/PNG/per-page-md are gitignored, they get backed up. **Do NOT pre-emptively delete raw scans after processing.** Leave them on disk; backup catches them; orchestrator/user may decide later to prune.

---

## Numbered steps (must execute in order)

### Step 1 — Worktree setup

```bash
STAMP=$(date +%Y%m%dT%H%M%S)
WT=".worktrees/dispatch/gemini/etymology-phase-2-bulk-ocr-${STAMP}"
git worktree add "$WT" -b feat/etymology-phase-2-bulk-ocr main
cd "$WT"
```

### Step 2 — Configure worktree's Gemini CLI to read gitignored binaries

```bash
mkdir -p .gemini
cat > .gemini/settings.local.json <<'EOF'
{
  "fileFiltering": {
    "respectGitIgnore": false
  }
}
EOF
```

Note: write to `settings.local.json` (gitignored by default) NOT `settings.json` — this is a runtime override, not project policy.

Verify before any OCR call:

```bash
# Should succeed (image reads via @path)
echo "in 1 sentence describe the rightmost top headword" \
  | gemini -p "@data/raw/esum/jp2-staging/tom 5 (Р - Т)_jp2/tom 5 (Р - Т)_0216.jp2" \
           --model gemini-2.5-flash --output-format text -y 2>&1 | tail -3
```

If the response says "ignored by configured ignore patterns": fix the settings file before continuing.

### Step 3 — Download remaining JP2 ZIPs (vol 1, 2, 3, 4, 6 — vol 5 already on main)

```bash
mkdir -p data/raw/esum/jp2-staging
cd data/raw/esum/jp2-staging

# vol 5 already on disk from Phase 1 — copy or symlink
if [ ! -f etslukrmov5_jp2.zip ]; then
  cp ../../../../../data/raw/esum/jp2-staging/etslukrmov5_jp2.zip . || true
fi

for n in 1 2 3 4 6; do
  [ -f "etslukrmov${n}_jp2.zip" ] && continue  # idempotent
  url="https://archive.org/metadata/etslukrmov${n}"
  jp2_file=$(curl -s "$url" | python3 -c "
import sys, json
m = json.load(sys.stdin)
for f in m['files']:
    if f['name'].endswith('_jp2.zip'):
        print(f['name']); break
")
  enc=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$jp2_file")
  echo "Downloading vol $n: $jp2_file"
  curl -L -o "etslukrmov${n}_jp2.zip" \
    "https://archive.org/download/etslukrmov${n}/${enc}" --progress-bar
done

cd -
```

Expected: ~600 MB net new (vol 5 already 115 MB on disk).

**Verifiable claim 1:** `ls -lh data/raw/esum/jp2-staging/*.zip` — 6 ZIPs totalling ~720 MB.

### Step 4 — Extract all volumes

```bash
cd data/raw/esum/jp2-staging
for n in 1 2 3 4 5 6; do
  zip="etslukrmov${n}_jp2.zip"
  [ -f "$zip" ] || continue
  [ -d "tom ${n} (*"*_jp2 ] && continue  # idempotent (skip if extracted)
  unzip -q "$zip"
done
cd -
```

### Step 5 — Decode every JP2 → PNG in parallel (idempotent)

`opj_decompress` is single-threaded (~37 ms/page); use xargs parallelism.

```bash
find data/raw/esum/jp2-staging -name "*.jp2" | \
  xargs -n 1 -P 8 -I {} bash -c '
    src="$1"
    png="${src%.jp2}.png"
    [ -f "$png" ] && exit 0  # idempotent
    opj_decompress -i "$src" -o "$png" >/dev/null 2>&1
  ' _ {}
```

**Verifiable claim 2:** `find data/raw/esum/jp2-staging -name "*.png" | wc -l` — ~4,200.

### Step 6 — Write the bulk OCR orchestrator

Create `scripts/etymology/bulk_ocr_gemini.py` (NEW file under `scripts/etymology/`, NOT `scripts/` root). Required behavior:

```python
"""Bulk Gemini-2.5-Flash OCR over decoded ESUM JP2 pages.

Idempotent: skips pages whose .md output file already exists.
Quota-aware: detects daily-quota exhaustion → emits QUOTA_HALT to JSONL log → exits 2.
Rate-limited: at most 12 concurrent gemini subprocesses (margin under the 15 RPM cap).
"""
```

Key requirements:

1. **Input:** walks `data/raw/esum/jp2-staging/*_jp2/*.png` in deterministic sorted order.
2. **Output:** `data/raw/esum/gemini-ocr/vol{N}/p{NNNN}.md` per page; concatenated `data/raw/esum/vol{N}-gemini.txt` per volume after all pages of that volume finish.
3. **Concurrency:** `asyncio.Semaphore(12)` wrapping `asyncio.create_subprocess_exec`. Hard-cap at 12 to leave headroom under the 15 RPM Free-tier rate.
4. **Per-call command:** `gemini -p "@<png-path-relative>" --model gemini-2.5-flash --output-format text -y`, stdin = `audit/etymology-ocr-feasibility/prompts/transcription-v1.txt`.
5. **Log:** one JSONL line per page to `audit/etymology-ocr-feasibility/bulk-run-log.jsonl`:
   - `{"event": "ok", "page": "vol5/p0216", "duration_s": 24.3, "bytes_out": 3401}`
   - `{"event": "error", "page": "...", "stderr_tail": "...", "retry_after": null}`
   - `{"event": "QUOTA_HALT", "page": "vol2/p0089", "stderr_tail": "...", "consecutive_quota_errors": 3}`
   - `{"event": "summary", "total": N, "ok": N, "error": N, "duration_s": T}` at end of run
6. **Retry policy** (per page):
   - Transient errors (HTTP 5xx, network timeout, `UNAVAILABLE`): exponential backoff 1, 2, 4, 8, 16, 32 s, max 5 retries.
   - Rate-minute errors (`RequestsPerMinute` / `60s` window): sleep 60 s then retry, max 3 retries.
   - **Daily-quota errors** (stderr contains any of: `Quota exceeded for quota metric.*Daily`, `Quota exceeded for quota metric.*PerDay`, `RESOURCE_EXHAUSTED.*daily`, `requests_per_day`): **DO NOT RETRY.** Increment a process-level counter `consecutive_quota_errors`. If counter reaches **3**, halt.
7. **Halt action:** when daily-quota-error counter hits 3, OR a hard-auth error appears (`PERMISSION_DENIED`, `invalid_grant`):
   - Write `QUOTA_HALT` event with the last 30 lines of stderr.
   - Print to stderr:
     ```
     ============================================================
     QUOTA_HALT — Gemini daily quota likely exhausted.
     Last successful page: vol{N}/p{NNNN}
     Pages completed in this run: M / total
     Pages remaining: K
     To resume: rotate the Gemini OAuth account, then re-run:
       cd <worktree>
       gemini /auth   # or gemini login --account other@account
       .venv/bin/python scripts/etymology/bulk_ocr_gemini.py
     The script will skip already-completed pages.
     ============================================================
     ```
   - Exit code 2 (distinct from generic error exit 1).

### Step 7 — Run the bulk OCR

```bash
.venv/bin/python scripts/etymology/bulk_ocr_gemini.py 2>&1 | tee /tmp/bulk-ocr-run.log
RC=$?
if [ $RC -eq 2 ]; then
  echo "QUOTA_HALT — orchestrator must notify user to rotate account"
  exit 2  # propagate to dispatcher so the monitoring loop sees it
fi
```

**Wall-time expectation:** at 12 concurrent, 25 s/call → ~700 pages/hr. **4,200 pages = ~6 h sequential wall**, but daily-quota wall hits at 1,500 pages → first session ≈ 2 h then QUOTA_HALT. Plan for 2-3 account rotations.

**Verifiable claim 3:** `wc -l audit/etymology-ocr-feasibility/bulk-run-log.jsonl` ≥ pages completed.

### Step 8 — On final successful pass (no QUOTA_HALT pending)

Concatenate per-page MD into per-volume text source:

```bash
for n in 1 2 3 4 5 6; do
  out="data/raw/esum/vol${n}-gemini.txt"
  [ -d "data/raw/esum/gemini-ocr/vol${n}" ] || continue
  ls data/raw/esum/gemini-ocr/vol${n}/p*.md | sort | xargs cat > "$out"
done
ls -lh data/raw/esum/vol*-gemini.txt
```

**Verifiable claim 4:** 6 `vol{N}-gemini.txt` files exist, total size ~25 MB.

### Step 9 — Re-ingest into sources.db

Modify or add a flag to `scripts/ingest/esum_ingest.py` so it can read from `vol{N}-gemini.txt` instead of `vol{N}.txt`. Replace (do not append). The parser layer should be format-agnostic since we used a faithful transcription prompt.

```bash
.venv/bin/python scripts/ingest/esum_ingest.py --source-suffix gemini --replace
```

**Verifiable claim 5:** `sqlite3 data/sources.db "SELECT COUNT(*) FROM esum_etymology_meta;"` — row count, was 29,171 before.

### Step 10 — Tighten cognate-form extractor

In `scripts/etymology/extract_cognate_forms.py` reject:
- Tokens containing any digit.
- Tokens that VESUM lemmatizes as Ukrainian function words.
- Tokens shorter than 2 characters.
- Tokens that are purely punctuation.

Run extractor and emit coverage delta:

```bash
.venv/bin/python scripts/etymology/extract_cognate_forms.py
sqlite3 data/sources.db "SELECT COUNT(*) FROM esum_cognate_forms WHERE forms IS NOT NULL AND LENGTH(forms) > 2;"
```

**Verifiable claim 6:** Coverage metric: 18,936 → {new} rows with non-empty cognate forms; report % change.

### Step 11 — 20-entry programmatic spot-check (BLOCKING gate)

```python
import random, json
random.seed(2001)  # deterministic, reproducible
sample_slugs = random.sample(all_slugs, 20)
```

For each slug:
- Render the page in dev mode: `cd starlight && npm run dev` (background)
- HTTP GET `http://localhost:4321/etymology/<slug>/`
- Check: cognate table non-empty AND every cognate row matches `^[a-zA-ZА-ЯҐЄІЇа-яґєії̂̀́̈̃чё\s\*\.\-\(\)]+$`

Write verdict table to `audit/etymology-ocr-feasibility/phase-2-spot-check.md`.

**HARD GATE:** ≥18/20 pass. If <18/20: halt, do NOT commit ingest output, write `PHASE_2_SPOT_CHECK_FAILED` to log, exit non-zero.

### Step 12 — Strip fabricated featured-card glosses

In `starlight/src/pages/etymology/index.astro`, replace each `gloss:` string with text actually derived from the new manifest (the first ~80 chars of the entry body) OR with a neutral `Том N, с. K` label only — never with orchestrator-fabricated linguistic claims like "псл. *voda".

The slug-verification vitest at `starlight/tests/unit/etymology-featured-slugs.test.ts` must continue to pass.

### Step 13 — Rebuild manifest

```bash
.venv/bin/python scripts/etymology/build_data_manifest.py
ls -lh starlight/src/data/etymology-manifest.json  # ~27 MB
```

### Step 14 — Tests + ruff + lint

```bash
.venv/bin/ruff check scripts/etymology/ scripts/ingest/
.venv/bin/python -m pytest tests/ -k "etymology or esum or russicism" -v
(cd starlight && npm run test:unit -- --run etymology-featured-slugs)
```

All three must pass.

**Verifiable claim 7:** raw `pytest ... N passed in M.MMs` line and raw `All checks passed!` for ruff.

### Step 15 — Backup raw scans (optional, leaves on disk)

The raw JP2/PNG/per-page md files are gitignored but `scripts/backup-data.sh` rsyncs them to Google Drive. **Do NOT delete the raw scans** after processing — the user may want them for re-runs.

If `scripts/backup-data.sh` exists at the worktree, the orchestrator (NOT this dispatch) runs it after merge.

### Step 16 — Commit + push + PR

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat(etymology): Phase 2 — re-OCR all 6 ESUM volumes with Gemini-2.5-Flash

Closes Phase 2 of #2001. Replaces Tesseract-era DjVu OCR with
gemini-2.5-flash transcription across all 4,200 pages.

Phase 1 verdict (PR #2004): Flash 2.5 at 90% exact / 100% plausible
cognate recovery, matching Pro and on free-tier quota.

Pipeline:
1. JP2 ZIP download from Archive.org (6 vols, ~720 MB)
2. opj_decompress JP2 → PNG (~4,200 pages, parallel)
3. Gemini-2.5-Flash OCR at concurrency 12 (~6 h wall, ~3 account-day rotations)
4. Re-ingest into sources.db (esum_etymology_meta rebuilt)
5. Tightened cognate-form regex
6. 20-entry deterministic-random spot-check
7. Manifest rebuild (~27 MB)
8. Stripped fabricated landing-card glosses (#M-4 cleanup)

Manifest delta:
  esum_etymology_meta: 29,171 → {NEW}
  esum_cognate_forms (non-empty): 18,936 → {NEW}

Per-page Gemini output kept locally in data/raw/esum/gemini-ocr/
(gitignored; backed up by scripts/backup-data.sh to Google Drive).
Concatenated vol{N}-gemini.txt files committed as new source-of-truth.

Co-Authored-By: Gemini 2.5 Flash
EOF
)"
git push -u origin feat/etymology-phase-2-bulk-ocr
gh pr create --title "feat(etymology): Phase 2 — re-OCR all 6 ESUM volumes with Gemini-2.5-Flash" \
  --body "$(cat <<'BODY'
Closes Phase 2 of #2001.

## Quantified delta vs main
{fill from claim 5/6}

## Test plan
- [x] Bulk OCR clean (failure rate {X}%, < 5% halt threshold)
- [x] No QUOTA_HALT pending (or document rotations performed)
- [x] Re-ingest rebuilt esum_etymology_meta with {N} rows
- [x] Spot-check {N}/20 pass
- [x] vitest etymology-featured-slugs pass
- [x] pytest etymology + esum + russicism pass
- [x] Ruff clean

Per-page Gemini outputs at data/raw/esum/gemini-ocr/ are gitignored
but backed up via scripts/backup-data.sh.

🤖 Generated with [Gemini CLI](https://geminicli.com)
BODY
)"
```

**Verifiable claim 8:** raw URL output from `gh pr view --json url`.

---

## Verifiable-claims preamble (per #M-4)

| Claim | Tool | Evidence format |
|---|---|---|
| 6 JP2 ZIPs downloaded | `ls -lh data/raw/esum/jp2-staging/*.zip` | 6 lines, raw `ls` |
| ~4,200 PNGs decoded | `find ... -name "*.png" \| wc -l` | numeric |
| Bulk OCR ran clean | `tail -1 audit/etymology-ocr-feasibility/bulk-run-log.jsonl` | `{"event": "summary", ...}` |
| No outstanding QUOTA_HALT | `grep '"QUOTA_HALT"' bulk-run-log.jsonl \| tail -1` | empty, or last entry is `event: ok` after the halt |
| Re-ingest count | `sqlite3 data/sources.db "SELECT COUNT(*) FROM esum_etymology_meta;"` | numeric |
| Spot-check pass | `cat audit/.../phase-2-spot-check.md` | raw verdict table, 20 rows |
| Pytest pass | `pytest ... 2>&1 \| tail -3` | raw "N passed" line |
| Ruff clean | `ruff check ...` | raw "All checks passed!" |
| PR opened | `gh pr view --json url` | raw URL |

No claim about an artifact may be made without quoting the tool output that produced it. The PR body's test-plan checkboxes only get ticked from real tool output.

---

## Halt conditions (escalate to orchestrator)

| Trigger | Action |
|---|---|
| `QUOTA_HALT` (3 consecutive daily-quota errors) | Exit 2. Orchestrator sees the JSONL event + console message, notifies user to rotate Gemini account. **THIS IS THE EXPECTED PATH AT ~1,500 PAGES.** |
| Gemini OAuth permission_denied | Exit 2, same as quota — auth swap needed. |
| Failure rate > 5% on bulk run (over a 100-page rolling window) | Exit non-zero with `BULK_QUALITY_HALT` event. Investigate before continuing. |
| Spot-check < 18/20 pass | Exit non-zero with `PHASE_2_SPOT_CHECK_FAILED`, do NOT commit ingest output. |
| Any blocking CI fail on the resulting PR | Standard PR-fail flow; orchestrator triages. |
| Worktree has dirty pre-existing tree | Abort before any work — refuse to overwrite user state. |

---

## Budget

- **Gemini calls:** ~4,200 × gemini-2.5-flash. Free-tier daily quota = 1,500 RPD per account → expect 2-3 account rotations.
- **Wall time:** Per session ~2 h (until quota wall). End-to-end ≥6 h elapsed (with rotation breaks). Hard timeout on dispatch = 7200 s; we'll likely hit QUOTA_HALT and exit cleanly before that.
- **Disk:** +630 MB temp (JP2/PNG), +12 MB local intermediate (per-page .md), +25 MB committed (vol{N}-gemini.txt).
- **Network:** ~600 MB one-time download.

## Out of scope (gated on Phase 2 success)

- Document AI fallback. Phase 1 cleared the bar.
- New UI features (search, A-Z browse). Gated.
- Vol-1 page 413 (вода) as a standalone "worst case" test. Handled by the 20-entry random spot-check.
- Pruning raw scans from disk. Leave on disk; backup catches them; orchestrator decides later.
