# Dispatch brief: Claude calibration matrix expansion (12 cells)

**Agent:** Claude headless (claude-opus-4-7)
**Mode:** `--mode danger` (worktree-isolated)
**Base branch:** `claude-calibration-matrix` (already pushed; contains the OAuth-inherit harness fix)
**Task ID:** `claude-calibration-matrix-2026-05-17`

## Why this work

The Russianism judge calibration matrix at
`audit/2026-05-17-judge-calibration-matrix/REPORT.html` currently has 0
Anthropic cells. The user (Krisztian) asked to expand the leaderboard
with a Claude column so we can compare Claude against the existing
Grok / GPT-5.5 / Gemini-3.1-Pro winners.

Scope was narrowed to **12 cells** (3 production-relevant Claude
variants × 2 efforts × 2 MCP states, native_cli harness only) because:

- The full 8-model Claude family × all combinations = ~136 cells —
  bloated, lots of intermediate point-releases that don't inform
  routing decisions.
- The hermes lane is blocked by **#2036** — `hermes auth status anthropic`
  reports `logged in` but Claude calls return empty stdout while
  gpt-5.5 returns PONG. That's the silent-drop failure mode, not auth.
  Don't try the hermes lane — it will produce 6 more useless 0% rows.

## Deterministic claims this work will produce (#M-4)

| Claim | Deterministic evidence required |
|---|---|
| "12 cells ran successfully" | `ls audit/2026-05-17-judge-calibration-matrix/anthropic/*/*/native_cli/*.json \| wc -l` returns 12 |
| "0 cells errored" | grep `"errors": []` count matches 12 OR explicit error list per cell |
| "REPORT.html includes Anthropic" | `grep -c "claude-" audit/2026-05-17-judge-calibration-matrix/REPORT.html` ≥ 12 |
| "Tests pass" | raw `pytest` summary line |
| "Ruff clean" | raw `ruff check` final line |
| "PR opened" | raw `gh pr view --json url` URL line |

## Numbered execution steps

### 1. Worktree setup
The base branch `claude-calibration-matrix` already exists at origin
and contains the OAuth-inherit harness fix
(commit `8b57b9a800`). The dispatch system creates a worktree
automatically — verify with:

```
git rev-parse HEAD              # should be 8b57b9a800 or descendant
git log -1 --oneline            # should mention "OAuth-inherit path"
```

### 2. Data symlinks (CRITICAL — the worktree's data/ is sparse)

The harness reads `data/sources.db` (1.6 GB) and `data/vesum.db` from
`PROJECT_ROOT`. Sparse worktrees ship with empty placeholders. Symlink:

```
[ -L data/sources.db ] || { rm -f data/sources.db; ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/sources.db data/sources.db; }
[ -L data/vesum.db ]   || { rm -f data/vesum.db;   ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/vesum.db   data/vesum.db; }
ls -la data/sources.db data/vesum.db    # confirm symlinks point to real files
```

### 3. Calibration cases fetch

The harness reads cases from `origin/pr-2006`. If that ref isn't in
your worktree's local refs, fetch it:

```
git rev-parse origin/pr-2006 >/dev/null 2>&1 || \
  git fetch origin 'refs/pull/2006/head:refs/remotes/origin/pr-2006'
```

### 4. Output directory

Cells write to the EXISTING report directory so the final REPORT.html
includes all 30 prior cells PLUS the new 12. **Do not change
`--out-dir`** — the path is hard-coded in the harness default.

```
ls audit/2026-05-17-judge-calibration-matrix/    # confirm google/, openai/, xai/ exist (REPORT.html/md from prior run)
```

### 5. Run the matrix (12 cells, ~30–45 min wall-time)

Use `--max-parallel 2` to stay conservative on Anthropic rate limits.
Use `--resume` so if the run is interrupted, restart picks up where it
left off (cells with valid JSON are skipped).

```
# venv symlinked into worktree by delegate.py
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --families anthropic \
  --models claude-opus-4-7,claude-sonnet-4-6,claude-haiku-4-5-20251001 \
  --harnesses native_cli \
  --efforts medium,high \
  --mcp-states with_mcp,without_mcp \
  --max-parallel 2 \
  --resume
```

This generates 12 per-cell JSON files PLUS rebuilds REPORT.md /
REPORT.html across ALL cells (prior 30 + new 12 = 42).

### 6. Verify the run completed

```
ls audit/2026-05-17-judge-calibration-matrix/anthropic/*/native_cli/*.json | wc -l
# expect: 12

jq -r '.scores | "F1=\(.f1) P=\(.precision) R=\(.recall) acc=\(.case_acc)"' \
  audit/2026-05-17-judge-calibration-matrix/anthropic/*/native_cli/*.json
# expect: 12 lines of scores, no judge_errors

grep -c "claude-" audit/2026-05-17-judge-calibration-matrix/REPORT.html
# expect: at least 12 (one row per cell)
```

### 7. Tests + lint

```
# venv symlinked into worktree by delegate.py
.venv/bin/python -m pytest tests/audit/test_judge_calibration_matrix.py -q
.venv/bin/ruff check scripts/audit/judge_calibration_matrix.py
```

Both must show raw pass output (`6 passed`, `All checks passed!`).

### 8. Commit

The repo policy forbids `git add -A` (might capture sensitive files).
Add specific paths:

```
git add audit/2026-05-17-judge-calibration-matrix/
git commit -m "$(cat <<'EOF'
feat(audit): add 12 Claude cells to Russianism calibration matrix

Expands the calibration leaderboard with 3 production-relevant
Claude variants (opus-4-7, sonnet-4-6, haiku-4-5) × 2 efforts
(medium, high) × 2 MCP states. Native_cli harness only — the
hermes anthropic lane is blocked by #2036 (silent drop despite
"logged in" status).

Run details:
- 12 cells, ~XX min wall-time
- Max parallel 2 (rate-limit conservative)
- OAuth-inherited from headless worker session (no API key)

Adds Anthropic family to the existing Gemini/GPT/Grok comparison.
Top finding: <fill in after seeing scores>

Refs #2036 (hermes anthropic silent drop — separate fix needed).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 9. Push

```
git push -u origin claude-calibration-matrix
```

### 10. Open PR (do NOT auto-merge)

```
gh pr create --title "feat(audit): Claude calibration matrix expansion (12 cells)" --body "$(cat <<'EOF'
## Summary
- Adds 12 Anthropic cells to the Russianism judge calibration matrix
- 3 models (opus-4-7, sonnet-4-6, haiku-4-5) × 2 efforts × 2 MCP states
- Harness fix: OAuth-inherit path (no API key needed when run from a Claude session)

## Result preview
Top finding: <fill in after seeing scores>

REPORT.html: artifacts/audit/2026-05-17-judge-calibration-matrix/REPORT.html

## Test plan
- [ ] pytest tests/audit/test_judge_calibration_matrix.py — pass
- [ ] ruff check scripts/audit/judge_calibration_matrix.py — pass
- [ ] manual: open REPORT.html, confirm 12 Anthropic rows present in leaderboard
- [ ] manual: confirm no judge_error verdicts in Failure Log section

## Known blockers (not in scope)
- Hermes anthropic lane: blocked by #2036 (silent drop). The 12 hermes
  cells we'd normally add are NOT in this PR. Filed as follow-up.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" --base main
```

**Do NOT pass `--allow-merge` or run `gh pr merge`** — Krisztian wants
to read the report and decide.

## Failure handling

- If any cell returns `judge_error` (rate limit, network blip), the
  `--resume` flag lets you re-run the same command and it picks up
  only the failed cells. Don't manually delete JSONs unless they're
  malformed.
- If the smoke run already passed in this worktree before dispatch,
  the OAuth path works. If you see "Not logged in" errors, something
  is wrong with the worker's session — STOP and report, don't try
  workarounds.
- Hard budget: if wall-time exceeds 90 minutes, STOP, report what
  cells completed, and we'll continue in a follow-up dispatch.

## What you do NOT do

- Do NOT touch `.bash_secrets` or any env file. The OAuth comes from
  `~/.claude/`, which is already set up.
- Do NOT enable the hermes lane "to see if it works now" — #2036 is
  confirmed live as of 17:09 UTC on 2026-05-16. The status command is
  lying.
- Do NOT auto-merge the PR.
- Do NOT modify cells from prior runs (google/, openai/, xai/) —
  they're the existing baseline.
