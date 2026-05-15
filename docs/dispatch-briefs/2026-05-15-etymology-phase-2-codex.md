# Dispatch Brief — Etymology Phase 2 (Codex re-fire)

**Date:** 2026-05-15
**Issue:** [#2001](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2001) — Re-OCR all 6 ESUM volumes
**Phase 1:** PR #2004 merged. Gemini-2.5-flash wins at 90% exact / 100% plausible.
**Previous Gemini dispatch:** killed by silence-timeout (curl `--progress-bar` writes to stderr; no stdout heartbeat).
**Target agent:** **Codex** (script-writing + robust orchestration, NOT Gemini's lane).
**Mode:** danger. **Worktree:** mandatory.

## What's already done — DO NOT REDO

- All 6 ESUM JP2 ZIPs are downloaded to `data/raw/esum/jp2-staging/` on main project. ~2.0 GB total. Verify with `ls -lh data/raw/esum/jp2-staging/*.zip` — must see 6 files: `etslukrmov{1..6}_jp2.zip`.
- Vol 5 is already extracted (`tom 5 (Р - Т)_jp2/` directory present).
- Phase 1 outputs (REPORT.md, scripts, prompts) live in `audit/etymology-ocr-feasibility/` from PR #2004.
- The transcription prompt at `audit/etymology-ocr-feasibility/prompts/transcription-v1.txt` is the same prompt used for Phase 1 — reuse verbatim.

## Job

Write **`scripts/etymology/bulk_ocr_gemini.py`** (new file, in `scripts/etymology/`, NOT in `scripts/` root — the No-new-root-scripts CI gate enforces) that does:

1. Extract any not-yet-extracted JP2 ZIPs (vols 1, 2, 3, 4, 6).
2. Decode every JP2 → PNG via `opj_decompress` (idempotent: skip pages whose PNG exists).
3. For every PNG that has no corresponding output, call `gemini -p "@<png>" --model gemini-2.5-flash --output-format text -y` with stdin = the transcription prompt.
4. Save each Gemini response to `data/raw/esum/gemini-ocr/vol{N}/p{NNNN}.md`.
5. On per-volume completion, concatenate `data/raw/esum/gemini-ocr/vol{N}/p*.md` → `data/raw/esum/vol{N}-gemini.txt`.
6. Halt cleanly with exit code **2** when the free-tier daily quota is exhausted (1,500 RPD), emitting a clear stderr message telling the user to rotate Gemini OAuth and re-run.

## Critical constraints (these are why the last dispatch died)

### Constraint 1 — STDOUT HEARTBEAT EVERY PHASE

The dispatcher's silence-timeout watches **stdout** (not stderr). The previous dispatch died because the bash brief used `curl --progress-bar` which writes to stderr only. **Every phase of your Python script MUST emit a stdout line at least every 30 seconds.** Concretely:

- ZIP extraction loop: `print(f"extracting vol{n} ({i}/{total})", flush=True)` per ZIP.
- JP2 → PNG decode loop: `print(f"decoded vol{n}/p{idx:04d} ({i}/{total})", flush=True)` every page, OR a counter every 20 pages.
- OCR loop: `print(f"ocr vol{n}/p{idx:04d} ok duration={d:.1f}s", flush=True)` per page.
- Any retries / waits / backoffs: `print(f"backoff vol{n}/p{idx:04d} attempt={a} sleep={s}s", flush=True)`.

`flush=True` is mandatory — Python buffers stdout when piped.

### Constraint 2 — IDEMPOTENT RESUME

The script will be re-run after every account rotation. Skip work that's already done:

- ZIP extraction: skip if `{name}_jp2/` directory exists with ≥ expected number of `.jp2` files.
- JP2 decode: skip per-file if matching `.png` file already exists with size > 0.
- OCR call: skip per-file if matching `.md` file already exists with size > 0.

A fresh invocation should be a no-op if all phases are complete; should resume from where it stopped otherwise.

### Constraint 3 — QUOTA DETECTION

Free-tier `gemini-2.5-flash` limits: **15 RPM / 1,500 RPD per account**. Quota detection:

- **Daily quota** (HALT): stderr from `gemini` contains any of:
  - `Quota exceeded for quota metric.*Daily`
  - `Quota exceeded for quota metric.*PerDay`
  - `RESOURCE_EXHAUSTED.*daily`
  - `requests_per_day`
  - `PERMISSION_DENIED`
  - `invalid_grant`

  Action: track `consecutive_quota_errors` process counter. On the **3rd** consecutive daily-quota error, halt:
  ```
  ============================================================
  QUOTA_HALT — Gemini daily quota likely exhausted.
  Last successful page: vol{N}/p{NNNN}
  Pages completed this run: M / total
  Pages remaining: K
  Resume: gemini /auth (swap to another Google account), then re-run:
    .venv/bin/python scripts/etymology/bulk_ocr_gemini.py
  Idempotent — already-completed pages will be skipped.
  ============================================================
  ```
  Exit code 2.

- **Per-minute rate limit** (BACKOFF + RETRY): stderr contains `RequestsPerMinute` / `60s`. Sleep 60s, retry. Max 3 retries per page.

- **Transient errors** (BACKOFF + RETRY): HTTP 5xx, network timeout, `UNAVAILABLE`, `INTERNAL`. Exponential backoff: 1, 2, 4, 8, 16, 32 s. Max 5 retries.

### Constraint 4 — CONCURRENCY ≤ 10

Use `asyncio.Semaphore(10)` wrapping `asyncio.create_subprocess_exec`. Free-tier is 15 RPM — 10-concurrent leaves headroom. The OCR call itself takes ~25 s/page, so 10-concurrent yields ~24 pages/min wall = below the RPM cap.

### Constraint 5 — LOG TO JSONL

Append one line per page to `audit/etymology-ocr-feasibility/bulk-run-log.jsonl`:

- Per-page ok: `{"event": "ok", "page": "vol5/p0216", "duration_s": 24.3, "bytes_out": 3401}`
- Per-page error: `{"event": "error", "page": "...", "stderr_tail": "...", "retries": N}`
- Quota halt: `{"event": "QUOTA_HALT", "page": "...", "consecutive_quota_errors": 3}`
- Final summary: `{"event": "summary", "total": N, "ok": N, "error": N, "duration_s": T}`

## Steps

1. Worktree setup. `git worktree add` etc.
2. **Configure worktree's gemini settings**:
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
   This is required — Gemini CLI's `@path` image input goes through `read_file` tool which by default respects `.gitignore`. Our PNGs are gitignored. Without this override, image reads will silently fail and Gemini will hallucinate.
3. Verify the existing ZIPs are visible from the worktree by checking `ls -lh ../../../data/raw/esum/jp2-staging/*.zip` — but the script will operate from the **worktree** so it needs the ZIPs visible at its own `data/raw/esum/jp2-staging/`. **Option A:** create symlinks. **Option B:** copy. **Recommended: symlink** the directory:
   ```bash
   mkdir -p data/raw/esum
   ln -sf ../../../../data/raw/esum/jp2-staging data/raw/esum/jp2-staging
   ```
4. Write `scripts/etymology/bulk_ocr_gemini.py` per the constraints above.
5. **Dry-run sanity check** — modify the script to support `--dry-run` that walks every input PNG and prints what it would do (skip vs OCR) without making any API call. Run dry-run first: `python scripts/etymology/bulk_ocr_gemini.py --dry-run | head -30`. Confirm the page counter looks right (~4,200 total).
6. **Smoke run** — re-run Phase 1's two test pages through the new script (`--only vol5/p0216,vol5/p0221`) and diff against the Phase 1 outputs in `audit/etymology-ocr-feasibility/raw-outputs/p0216-gemini-vision.txt` / `p0221-gemini-vision.txt` (these were on gemini-3-pro-preview; 2.5-flash may differ slightly but should produce the same cognate forms). Confirm the script's OCR loop actually works end-to-end before running the bulk job.
7. **Run the bulk job**: `python scripts/etymology/bulk_ocr_gemini.py 2>&1 | tee /tmp/bulk-run.log`. **Will halt at QUOTA_HALT after ~1,500 pages — that is the EXPECTED outcome of this dispatch.** Do not retry from the same account; let the script exit 2 with the rotation message.
8. **Commit + push + PR with no auto-merge** — at the point of dispatch exit (either bulk run complete OR QUOTA_HALT), commit:
   - `scripts/etymology/bulk_ocr_gemini.py`
   - `audit/etymology-ocr-feasibility/bulk-run-log.jsonl` (the run log)
   - `data/raw/esum/vol{N}-gemini.txt` for any volumes that finished completely
   - The per-page `.md` files in `data/raw/esum/gemini-ocr/` are **gitignored**, do NOT commit them
9. PR body: report total pages processed, pages remaining, halt cause if QUOTA_HALT, link to bulk-run-log.jsonl summary line.

## Gitignore

Add these to `.gitignore` (the staging dir was already added for Phase 1; the gemini-ocr/ output dir is new):

```
data/raw/esum/gemini-ocr/
```

`data/raw/esum/jp2-staging/` is already gitignored from PR #2004.

## Verifiable-claims preamble (per #M-4)

| Claim | Tool | Evidence |
|---|---|---|
| All 6 ZIPs visible to the script | `ls -lh data/raw/esum/jp2-staging/*.zip` | 6 lines of raw `ls` output |
| All JP2 decoded | `find data/raw/esum/jp2-staging -name "*.png" \| wc -l` | numeric |
| Pages processed | `wc -l audit/etymology-ocr-feasibility/bulk-run-log.jsonl` | numeric (line count = pages attempted) |
| Halt reason (if applicable) | `grep '"event":"QUOTA_HALT"' audit/etymology-ocr-feasibility/bulk-run-log.jsonl` | raw match line |
| Smoke pages match Phase 1 ground truth | `diff` against `audit/etymology-ocr-feasibility/raw-outputs/p0216-gemini-vision.txt` (allow minor whitespace diff) | diff summary |
| Ruff clean | `ruff check scripts/etymology/` | raw `All checks passed!` |
| PR opened | `gh pr view --json url` | raw URL |

No claim about an artifact without quoting the producing tool output.

## Halt conditions (escalate to orchestrator)

| Trigger | Action |
|---|---|
| QUOTA_HALT | Exit 2 with full halt message. Orchestrator sees stdout + JSONL event, alerts user to rotate Gemini account. **EXPECTED to fire around page 1,500.** |
| Smoke test diff > 5% character mismatch from Phase 1 ground truth | Halt before bulk run. Investigate prompt/model regression. |
| Failure rate > 5% on a 100-page rolling window | Halt with `BULK_QUALITY_HALT` event. |

## Out of scope (gated on Phase 2 ingest finishing across all rotations)

- Re-ingest into `sources.db` (will happen in a follow-up dispatch once all 6 vols' `-gemini.txt` files are committed).
- Cognate-form regex tightening.
- 20-entry spot-check.
- Stripping fabricated landing-card glosses.
- Manifest rebuild.

These wait for all volumes to OCR (multiple QUOTA_HALT / rotation cycles).

## Branch + commit conventions

- Branch: `feat/etymology-phase-2-bulk-ocr`
- Commit subject: `feat(etymology): Phase 2 bulk OCR script + first run (#2001)` (or with `(partial — QUOTA_HALT at vol{N})` suffix on halt)
- X-Agent trailer per AGENTS.md convention
