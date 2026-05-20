# Issue #2001 ESUM re-OCR — orchestrator handoff (2026-05-20)

> **Scope:** OCR project (issue #2001) only. Continuation of `docs/session-state/2026-05-19-issue-2001-ocr-handoff.md`.
> Does **not** touch the main session handoff or `current.md`.

## Immediate next action

**Waiting on user OAuth rotation.** OCR halted via QUOTA_HALT at 07:37 local on 2026-05-20.

When user signals "rotated" / "go" / similar — or if you see PID active under a new run — refire:

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
nohup .venv/bin/python -u scripts/etymology/bulk_ocr_gemini.py \
  --concurrency 1 --rpm 8 --model gemini-2.5-flash \
  >> /tmp/bulk-ocr-2026-05-17-evening.log 2>&1 < /dev/null & disown
```

Verify with `tail -20 /tmp/bulk-ocr-2026-05-17-evening.log` after a few seconds. PID check before refire per **#M-9** (never refire while previous process alive).

## State frozen at QUOTA_HALT (07:37)

| Volume | On-disk pages | Target | % | Notes |
|---|---|---|---|---|
| vol1 | 634 | 634 | 100% ✅ | concatenated → `data/raw/esum/vol1-gemini.txt` (4.78 MB) |
| vol2 | 573 | 573 | 100% ✅ | concatenated → `data/raw/esum/vol2-gemini.txt` (4.98 MB) |
| vol3 | 553 | 553 | 100% ✅ | concatenated → `data/raw/esum/vol3-gemini.txt` (**26.8 MB inflated** — 9 pre-existing corrupt files still in place) |
| vol4 | 655 | 657 | 99.7% | 2 hard stragglers; NOT auto-concatenated (script requires 100%) |
| vol5 | 584 | 705 | 82.8% | many stragglers + 121 unattempted |
| vol6 | 0 | 569 | 0% | not started |

**Cumulative**: 2,999 / 3,691 (81.3%). **Pending**: 692.

Math note: per-vol sum (634+573+553+655+584+0) = 2,999 — this differs from earlier "2,968" reports because those reflected on-disk counts AFTER live quarantines but the per-vol count above is the raw filesystem count which includes some live quarantines not yet removed via this session's mv. Re-run a fresh `find` to get the authoritative count.

## What this session (refire-2 / 2026-05-19 19:13 → 2026-05-20 07:37) accomplished

- 278 net pages added under fresh tenant over ~12h25m (~22/hr avg)
- vol2 + vol3 concat artifacts written for the first time (auto-concat at QUOTA_HALT)
- **6 corrupt pages quarantined** via shadow uniqueness check (filter v2 missed all 6):
  - `_quarantine/2026-05-19-repetition-hallucination/vol5_p0182.md`
  - `_quarantine/2026-05-19-repetition-hallucination/vol5_p0335.md`
  - `_quarantine/2026-05-19-repetition-hallucination/vol5_p0403.md`
  - `_quarantine/2026-05-19-repetition-hallucination/vol5_p0442.md`
  - `_quarantine/2026-05-19-repetition-hallucination/vol5_p0548.md`
  - `_quarantine/2026-05-19-repetition-hallucination/vol5_p0608.md`
- Closeout brief authored: `docs/dispatch-briefs/2026-05-19-etymology-closeout-codex.md`
- Backup tarball pushed to `~/My Drive/learn-ukrainian-backups/esum-ocr-snapshot-2026-05-19.tar.gz` (18 MB, SHA256 verified)
- Identified critical filter gap (model repetition-loop bypasses v2; uniqueness ratio < 0.20 catches it)

## Sweep loop — verbatim

```bash
echo "=== OCR PID alive ==="
/bin/ps -ef | grep -E "bulk_ocr_gemini|gemini-cli" | grep -v grep

echo "=== log mtime + now ==="
ls -la /tmp/bulk-ocr-2026-05-17-evening.log
echo "now: $(date -u +%FT%TZ)  (local: $(date +%H:%M:%S))"

echo "=== log tail ==="
tail -25 /tmp/bulk-ocr-2026-05-17-evening.log

echo "=== per-vol counts ==="
for v in 1 2 3 4 5 6; do
  count=$(find data/raw/esum/gemini-ocr/vol$v -maxdepth 1 -name "p*.md" 2>/dev/null | wc -l | tr -d ' ')
  echo "vol$v: $count"
done

echo "=== transients count ==="
grep "category=transient" /tmp/bulk-ocr-2026-05-17-evening.log | wc -l | tr -d ' '
```

And the shadow uniqueness check (REQUIRED each sweep — filter v2 is blind to repetition-loop corruption):

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts/etymology')
from bulk_ocr_gemini import is_low_quality_output
from pathlib import Path
import subprocess, datetime
now = datetime.datetime.now()
thirty_ago = (now - datetime.timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M')
out = subprocess.run(['find', 'data/raw/esum/gemini-ocr', '-name', 'p*.md', '-not', '-path', '*/_quarantine/*', '-newermt', thirty_ago], capture_output=True, text=True)
files = [Path(f) for f in out.stdout.strip().split('\n') if f]
print(f'last 30 min: {len(files)} files  rate={len(files)/30*60:.1f}/hr')
bad_v2 = [str(f) for f in files if is_low_quality_output(f.read_text())]
print(f'filter v2 flagged: {len(bad_v2)}')
new_flags = []
for f in files:
    try:
        lines = [l for l in f.read_text().splitlines() if l.strip()]
        if len(lines) < 100: continue
        ratio = len(set(lines)) / len(lines)
        if ratio < 0.20:
            new_flags.append((f, len(lines), ratio))
    except: pass
print(f'shadow uniqueness flagged: {len(new_flags)}')
for f, n, r in new_flags: print(f'  {f} lines={n} ratio={r:.2f}')
"
```

If shadow flags any file → quarantine immediately:

```bash
QUAR=data/raw/esum/gemini-ocr/_quarantine/2026-05-19-repetition-hallucination
mv data/raw/esum/gemini-ocr/vol${N}/p${NNNN}.md "$QUAR/vol${N}_p${NNNN}.md"
```

## Decision tree on each sweep

- **Log mtime stale > 5 min while PID alive** → hang. `pkill -9 -f bulk_ocr_gemini && pkill -9 -f gemini-cli`, then refire.
- **PID gone + QUOTA_HALT in log** → schedule 3600s wake. Do NOT refire until user rotates OAuth.
- **PID gone, no QUOTA_HALT** → refire immediately (script is idempotent).
- **PID alive, log advancing, rate ≥ 10/hr, 0 filter flags** → schedule next 1500s wake.
- **Any filter flag (v2 OR shadow)** → quarantine, continue.
- **4+ consecutive new `category=transient retries=5` errors after current refire** → tenant saturation. SIGTERM (not SIGKILL), write user status, schedule 3600s wake.

## Operational knowledge — what we learned

### Two error categories matter

The script emits `error category=<kind> retries=<n>` lines. Two flavors:

| Category | Meaning | Action |
|---|---|---|
| `error` | Scan-shaped refusal / hard fail / quick give-up | Expected straggler. Most clear under fresh tenant. |
| `transient` | Rate limit / timeout / connection (= tenant saturation) | **Trigger for kill+rotate cycle.** 4 in a row = stop the run. |

Pre-refire run (~9:42 → 17:30) had 4 transients all clustered at the end (p0291, p0293, p0294 in old tenant). Post-refire run had 0 new transients until quota actually hit — clean tenant signal.

### Filter v2 has a gap; shadow uniqueness fills it

`is_low_quality_output()` was hardened by PRs #2115 + #2129 (refusal + completion-meta + repetition substring) but **misses repetition-loops of valid dictionary entries**. Signature: file ≥ 100 lines AND `len(set(non_empty_lines)) / len(non_empty_lines) < 0.20`. Six confirmed corruptions this session, all caught only by the shadow check.

Closeout brief step A adds this check to the real filter + tests. Until that lands, the shadow check IS the protection — run it every sweep.

### Pre-existing corruption (NOT from this session)

29 files across vol3+vol4+vol5 with same repetition-loop pattern from earlier runs (pre-refire). They sit IN PLACE in `data/raw/esum/gemini-ocr/vol{N}/p*.md` polluting the corpus. Step B of the closeout brief sweeps them up. **Do NOT manually quarantine them now** — that's closeout work.

To check current scope (purely informational):

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
suspects = []
for md in sorted(Path("data/raw/esum/gemini-ocr").glob("vol*/p*.md")):
    if "quarantine" in str(md): continue
    lines = [l for l in md.read_text().splitlines() if l.strip()]
    if len(lines) < 100: continue
    ratio = len(set(lines)) / len(lines)
    if ratio < 0.20:
        suspects.append((md, len(lines), ratio))
print(f"total suspects: {len(suspects)}")
from collections import Counter
by_vol = Counter(s[0].parts[-2] for s in suspects)
for v, c in sorted(by_vol.items()):
    print(f"{v}: {c}")
PY
```

Last measured: vol3=9, vol4=13, vol5=7. **vol1 + vol2 are clean** (verified — and that's why vol1+vol2-gemini.txt are reasonably sized).

### "Slow pages" are mostly invisible corruption events

When a page takes 10-20 min and "succeeds," check uniqueness. The model often gets into a loop, eventually emits 5000+ lines of repeated entries, gemini-cli returns when its stream closes, script writes it, filter passes it. The "slowness" IS the symptom. The fast pages tend to be the clean ones.

### Backup pattern (already done — DO NOT REDO unless OCR makes major progress)

```bash
STAMP=$(date +%F)
WORK=/tmp/esum-backup-$STAMP
TARBALL=/tmp/esum-ocr-snapshot-$STAMP.tar.gz
mkdir -p $WORK
# write MANIFEST.txt with page counts, hostname, git HEAD, restore notes
tar czf $TARBALL \
  --exclude="data/raw/esum/gemini-ocr/_quarantine" \
  -C / \
  tmp/esum-backup-$STAMP/MANIFEST.txt \
  Users/krisztiankoos/projects/learn-ukrainian/data/raw/esum/gemini-ocr \
  Users/krisztiankoos/projects/learn-ukrainian/data/raw/esum/vol*-gemini.txt \
  tmp/bulk-ocr-2026-05-17-evening.log
# verify gzip OK + SHA256
# cp into ~/Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com/My\ Drive/learn-ukrainian-backups/
```

Drive sync app is running — file appears in cloud automatically after cp.

Last backup: 2026-05-19 13:18 local (state was vol5=231, cumulative 2,642). Worth a fresh snapshot only if vol6 makes major progress; per-page md tree compresses ~5× so a vol6-complete snapshot would be ~30-40 MB.

## Closeout pipeline — when to dispatch

**Trigger condition**: vol5 + vol6 both reach ≥ ~95% (tolerance for ~5-10 hard stragglers per vol). Currently 82.8% + 0% — far from ready.

When ready, dispatch `docs/dispatch-briefs/2026-05-19-etymology-closeout-codex.md` to Codex per `delegate.py`:

```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent codex \
  --brief docs/dispatch-briefs/2026-05-19-etymology-closeout-codex.md \
  --mode danger
```

Brief covers: filter hardening (A) → quarantine sweep (B) → re-OCR under fresh tenant (C) → concat/ingest/regex/manifest/glosses/spot-check/PR (D-J).

## What this handoff is NOT

- NOT a refire trigger — refire requires user OAuth rotation signal
- NOT updating `docs/session-state/current.md`
- NOT touching MEMORY.md
- Continuation pointer for next orchestrator/wake on the OCR lane only

## Carry-over from yesterday's handoff (still valid)

- Concurrency rule (#M-9): never run > 1 local OCR at a time
- Single per-page failures are normal; clusters of consecutive failures = tenant signal
- Run history pattern: ~8-22h per OAuth tenant before QUOTA_HALT, then rotation required
- Stragglers tend to clear under new tenant (~80% recovery rate empirically)
