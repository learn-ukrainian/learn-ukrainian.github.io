# Dispatch brief: Opus-4.7 xhigh follow-up (2 cells)

**Agent:** Claude headless (claude-opus-4-7)
**Mode:** `--mode danger` (worktree-isolated)
**Base branch:** `main` (already contains the OAuth-inherit harness fix from PR #2044)
**Task ID:** `opus-xhigh-followup-2026-05-17`

## Why this work

User explicit ask: test claude-opus-4-7 at `xhigh` effort. The
previous run (PR #2044) tested medium+high only — the highest two
reasoning tiers (`xhigh`, `max`) were locked out for scope. Adding
`xhigh` × 2 MCP states = 2 cells.

Quality mandate: see if xhigh pushes opus past its current F1=0.828
ceiling, and whether it closes the case_acc gap (currently 0.917 = 1
miscalled case; grok-4.3/xhigh achieves 1.000).

NOTE: only `xhigh` is in scope, NOT `max`. User said "xhigh" by name.
Do not add `max` "for completeness" — that's scope creep.

## Deterministic claims this work will produce

| Claim | Evidence |
|---|---|
| "2 cells ran successfully" | `ls audit/2026-05-17-judge-calibration-matrix/anthropic/claude-opus-4-7/native_cli/xhigh-*.json \| wc -l` returns 2 |
| "0 cells errored" | grep `"errors": []` matches 2 |
| "REPORT.html includes xhigh rows" | `grep -c "xhigh" audit/2026-05-17-judge-calibration-matrix/REPORT.html` ≥ 2 |
| "Tests pass" | raw `pytest` summary |
| "Ruff clean" | raw `ruff check` final line |
| "PR opened" | raw `gh pr view --json url` URL line |

## Numbered execution steps

### 1. Worktree
Dispatch system creates `.worktrees/dispatch/claude/opus-xhigh-followup-2026-05-17/`
auto-branched from main. Verify the OAuth-inherit fix is present
(should be — landed in #2044 / commit `dbfe48c892`):

```
git log --oneline scripts/audit/judge_calibration_matrix.py | head -2
grep -q "CLAUDE_MATRIX_USE_BARE" scripts/audit/judge_calibration_matrix.py && echo "fix present" || echo "FIX MISSING — STOP"
```

### 2. Data symlinks (sparse worktree)

```
[ -L data/sources.db ] || { rm -f data/sources.db; ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/sources.db data/sources.db; }
[ -L data/vesum.db ]   || { rm -f data/vesum.db;   ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/vesum.db   data/vesum.db; }
```

### 3. Fetch calibration cases

```
git rev-parse origin/pr-2006 >/dev/null 2>&1 || git fetch origin 'refs/pull/2006/head:refs/remotes/origin/pr-2006'
```

### 4. Run the 2 cells

```
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --families anthropic \
  --models claude-opus-4-7 \
  --harnesses native_cli \
  --efforts xhigh \
  --mcp-states with_mcp,without_mcp \
  --max-parallel 2 \
  --resume
```

`--resume` ensures the existing 12 anthropic cells from PR #2044 are
NOT re-run. Only the 2 new `xhigh-*` cells get computed. REPORT.html
gets rebuilt across all 44 cells (30 prior + 12 from #2044 + 2 new).

### 5. Verify

```
ls audit/2026-05-17-judge-calibration-matrix/anthropic/claude-opus-4-7/native_cli/xhigh-*.json | wc -l
# expect: 2

jq -r '"\(.cell.effort)/\(.cell.mcp_state) F1=\(.scores.f1) P=\(.scores.precision) R=\(.scores.recall) acc=\(.scores.case_acc)"' \
  audit/2026-05-17-judge-calibration-matrix/anthropic/claude-opus-4-7/native_cli/xhigh-*.json
# expect: 2 lines, no judge_errors

grep -c "xhigh" audit/2026-05-17-judge-calibration-matrix/REPORT.html
# expect: ≥ 2
```

### 6. Tests + lint

```
.venv/bin/python -m pytest tests/audit/test_judge_calibration_matrix.py -q
.venv/bin/ruff check scripts/audit/judge_calibration_matrix.py
```

### 7. Commit

```
git add audit/2026-05-17-judge-calibration-matrix/
git commit -m "$(cat <<'EOF'
feat(audit): add opus-4-7 xhigh cells to calibration matrix

User-requested follow-up to PR #2044. Tests claude-opus-4-7 at the
xhigh effort tier × 2 MCP states (with/without). Closes the most
actionable quality gap: prior run locked to medium+high effort only.

Run details:
- 2 cells, native_cli, OAuth-inherit (no API key)
- Append-only to existing matrix via --resume
- REPORT.html now spans 44 cells

Key finding: <fill in after seeing scores — did xhigh push F1 past 0.828?>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 8. Push + open PR (no auto-merge)

```
git push -u origin <branch>
gh pr create --title "feat(audit): opus-4-7 xhigh cells (calibration matrix)" --body "$(cat <<'EOF'
## Summary
- Adds 2 cells: claude-opus-4-7 at xhigh effort × {with_mcp, without_mcp}
- Closes a quality gap from PR #2044 (which tested medium+high only)

## Result preview
- xhigh / with_mcp: F1=X.XXX, P=X.XX, R=X.XX, case_acc=X.XX
- xhigh / without_mcp: F1=X.XXX, P=X.XX, R=X.XX, case_acc=X.XX

Did xhigh push opus past its 0.828 F1 ceiling? <yes/no>
Did xhigh close the case_acc gap to grok's 1.000? <yes/no>

## Test plan
- [ ] pytest tests/audit/test_judge_calibration_matrix.py — pass
- [ ] ruff check scripts/audit/judge_calibration_matrix.py — pass
- [ ] manual: REPORT.html includes 2 new xhigh rows

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" --base main
```

**Do NOT auto-merge.** User reads results first.

## Hard rules

- ONLY `xhigh` effort. NOT `max`. NOT anything else.
- ONLY `claude-opus-4-7`. NOT other models.
- NOT the hermes harness (#2036 still live).
- NO rebuilds of existing 42 cells (use `--resume`).
- NO auto-merge.

## Budget note

xhigh is more expensive than high (more thinking tokens). 2 cells × 12
cases = 24 calls at xhigh. Stay under 30 min wall-time; if longer,
STOP and report what completed.
