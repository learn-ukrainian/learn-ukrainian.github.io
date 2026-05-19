# Issue #2001 ESUM re-OCR — slow-burn handoff (2026-05-19)

> **Scope:** OCR project (issue #2001) only. Does **not** touch the main
> session handoff or `current.md`. Other tracks (m20 build, Path 3,
> qwen integration, etc.) are unchanged from main-handoff state.

## Immediate next action

**User rotated the Gemini OAuth.** Refire the bulk runner from main:

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
nohup .venv/bin/python -u scripts/etymology/bulk_ocr_gemini.py \
  --concurrency 1 --rpm 8 --model gemini-2.5-flash \
  >> /tmp/bulk-ocr-2026-05-17-evening.log 2>&1 < /dev/null & disown
```

Then verify with `tail -20 /tmp/bulk-ocr-2026-05-17-evening.log` after ~60 s —
expect either `ocr vol... ok duration=Ns` (good) or `daily-quota-error`
(quota not actually reset; ScheduleWakeup 3600 s and retry).

If clean OCR starts, drop to 25-min monitoring cadence (see "Sweep loop" below).

## State at handoff (frozen at QUOTA_HALT #2, 07:38 local)

| Volume | Done | Target | % | Notes |
|---|---|---|---|---|
| vol1 | 634 | 634 | **100% ✅** | `data/raw/esum/vol1-gemini.txt` regenerated (4.78 MB) with all filter-v2 cleanups baked in |
| vol2 | 571 | 573 | 99.7% | 2 persistent-failure stragglers — new OAuth tenant may clear them, like vol3 did last cycle |
| vol3 | 552 | 553 | 99.8% | 1 straggler |
| vol4 | 632 | 657 | 96.2% | 25 stragglers |
| vol5 | 181 | 705 | 25.7% | mid-sweep |
| vol6 | 0 | 569 | 0% | not started |

**Cumulative**: 2,570 / 3,691 (69.6%). **Pending**: 1,121.

## Filter pipeline status

**Filter v2 is on main** — two PRs merged this session:

- **PR #2115** (refusal + completion-meta filter, merged 2026-05-17 21:29 UTC)
- **PR #2129** (repetition-hallucination filter, merged 2026-05-18 07:20 UTC)

Together they rejected **81 corrupt files** the original filter missed. All 81
were re-OCR'd cleanly under the hardened pipeline in this run. No quarantine
backlog currently — every known failure shape has been quarantined,
re-OCR'd, and verified clean.

Live filter behavior during the most recent ~22h run: **0 leaks landed on
disk**. The filter catches refusal/meta/repetition pre-write, retries up to
3× via the script's existing retry logic, then moves on.

## How the script behaves on refire

- **Idempotent** — scans `data/raw/esum/gemini-ocr/vol*/p*.md` at startup,
  pending = whatever's missing. Won't re-OCR finished pages.
- **Persistent-failure pages stay missing** — pages where Gemini consistently
  returns refusal/repetition will hit `error category=error retries=N` and
  be skipped after retries. Each refire retries them. Some clear on new
  tenant (~80% of vol3+vol4 stragglers cleared last OAuth swap; the 28
  remaining are likely scan-damage or hard-refusal).
- **On QUOTA_HALT**: process exits cleanly, calls `concatenate_completed_volumes()`
  which writes `data/raw/esum/vol{N}-gemini.txt` for any volume at 100% done.
- **No filter flags expected** — if any appear during the run, **quarantine
  immediately** to `data/raw/esum/gemini-ocr/_quarantine/<datestamp>-<reason>/`
  and investigate (new failure shape).

## Sweep loop (25-min cadence after first OCR confirmed clean)

```bash
echo "=== OCR PID alive ==="
/bin/ps -ef | grep -E "bulk_ocr_gemini|gemini-cli" | grep -v grep

echo "=== log mtime + now ==="
ls -la /tmp/bulk-ocr-2026-05-17-evening.log
echo "now: $(date -u +%FT%TZ)"

echo "=== log tail ==="
tail -20 /tmp/bulk-ocr-2026-05-17-evening.log

echo "=== per-vol counts ==="
for v in 1 2 3 4 5 6; do
  count=$(find data/raw/esum/gemini-ocr/vol$v -maxdepth 1 -name "p*.md" 2>/dev/null | wc -l | tr -d ' ')
  echo "vol$v: $count"
done

echo "=== halt+concat events ==="
grep -cE "QUOTA_HALT|BULK_QUALITY_HALT|concatenated vol" /tmp/bulk-ocr-2026-05-17-evening.log

echo "=== filter sweep last 30min ==="
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts/etymology')
from bulk_ocr_gemini import is_low_quality_output
from pathlib import Path
import subprocess, datetime
now = datetime.datetime.now()
thirty_ago = (now - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M')
out = subprocess.run(['find', 'data/raw/esum/gemini-ocr', '-name', 'p*.md', '-not', '-path', '*/quarantine/*', '-newermt', thirty_ago], capture_output=True, text=True)
files = [Path(f) for f in out.stdout.strip().split('\n') if f]
print(f'last 30 min: {len(files)} files  rate={len(files)/30*60:.1f}/hr')
bad = [str(f) for f in files if is_low_quality_output(f.read_text())]
print(f'flagged: {len(bad)}')
for b in bad: print(' ', b)
"
```

**Hang detection**: if log mtime > 5 min stale while PID still alive → gemini-cli
child is hung. `pkill -9 -f bulk_ocr_gemini && pkill -9 -f gemini-cli`, then refire.
Happened once at vol2/p0100 (~25 min hang). Recovery clean.

## Closeout pipeline (after all OCR done — DO NOT START until vol5/vol6 finish)

Per `docs/dispatch-briefs/2026-05-15-etymology-phase-2-codex.md`:

1. Concat per-page `.md` → `data/raw/esum/vol{N}-gemini.txt` (script handles
   automatically at halt; only need to verify all 6 files present and
   non-zero size after final run).
2. Re-ingest via `.venv/bin/python scripts/ingest/esum_ingest.py --source-suffix gemini --replace`
3. Tighten `scripts/etymology/extract_cognate_forms.py` regex (digit + Ukrainian
   function-word filters) — Codex dispatch.
4. Rebuild `starlight/src/data/etymology-manifest.json`.
5. Strip fabricated featured-card glosses in `starlight/src/pages/etymology/index.astro`.
6. 20-entry deterministic-random spot-check, **seed=2001**.
7. Single PR closing #2001.

## Concurrency rule (HARD)

**Max 1 local OCR process at a time** (user direction + #M-9). Never refire
without confirming the previous PID is gone. The script is idempotent so
zero risk of data loss from clean kills.

## Files of interest

- Script: `scripts/etymology/bulk_ocr_gemini.py` (29 LOC patch from #2115 + 77 LOC from #2129 already on main)
- Tests: `tests/etymology/test_bulk_ocr_quality.py` (11 tests, all green)
- Log: `/tmp/bulk-ocr-2026-05-17-evening.log` (~1 MB, append-only since 2026-05-17 19:30 local)
- Issue: `gh issue view 2001 --comments` for full history
- This session's QA findings: issue #2001 comments #4472282658 (first QA pass) and #4484753538 (second QUOTA_HALT milestone)

## Operator notes

- Run 1 (8.7h) → QUOTA_HALT, OAuth rotated by user.
- Run 2 (~22h) → QUOTA_HALT #2, vol1 re-concatenated with filter-v2 content.
- This is OCR run 3 about to start under the second OAuth rotation.
- Cumulative session: 4 runs total counting probe failures. ~30 hours of productive OCR time across them.
- ETA at observed 21 pages/hr: 1,121 / 21 ≈ 53 h continuous; realistic with halts: 3-4 more days.

## What this handoff is NOT

- NOT updating `docs/session-state/current.md`
- NOT updating any of the main 2026-05-19 session-state docs
- NOT touching MEMORY.md
- Just a continuation pointer for whoever picks up the OCR lane
