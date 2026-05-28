# Dispatch: fix codex-tools rollout-capture timezone bug (unblocks codex as the V7 scale writer)

**Agent:** codex · **Mode:** danger + worktree · **No auto-merge.**

## Why this matters
codex-tools must be the V7 SCALE writer (own weekly quota; claude-tools is unaffordable after 2026-06-15). You (codex) diagnosed this yourself in task `codex-writer-toolfix-20260529`. This brief turns that diagnosis into the merged fix.

## Verified ground truth (do NOT re-litigate — already confirmed deterministically)
- The failed build (`v7_build.py a1 my-morning --writer codex-tools --worktree`, worktree `.worktrees/builds/a1-my-morning-20260528-221218/`) wrote `writer_tool_calls.json == []` and failed the `mcp_tools_never_invoked` HARD gate.
- **The rollout is NOT callless.** File: `/private/tmp/claude-501/codex-v7-writer-501/sessions/2026/05/29/rollout-2026-05-29T00-12-26-019e70a5-5dc7-7f93-a92a-0f3c1b57d932.jsonl` (555 KB). It contains **14 `mcp__sources__` calls**: `verify_words ×4`, `get_chunk_context ×2`, `query_cefr_level ×2`, `check_russian_shadow ×1`, `query_pravopys ×1`, `search_images ×1`, `search_style_guide ×1`.
- **CORRECTION to your earlier message:** you wrote "this run still made zero `verify_words` calls" — that is WRONG. It made **4**. So codex BEHAVIOR is correct. The ONLY defect is **capture**. Do NOT spend effort forcing tool-use behavior that already works.
- **Root cause (confirmed in code):** rollout discovery uses **UTC date** dirs. Run was `2026-05-28T22:12Z` = `2026-05-29` Budapest local; Codex wrote `sessions/2026/05/29`; the adapter scanned UTC `2026/05/28` and missed it. This is why it was "38 one day, 0 the next" — it depends on whether the run straddles the UTC↔local date boundary.
  - `scripts/agent_runtime/adapters/codex.py::_check_rollout_liveness` (~L565): uses `datetime.now(UTC)` AND `Path.home() / ".codex"` (UNSCOPED home — second bug).
  - `scripts/agent_runtime/adapters/codex.py::_candidate_rollout_dirs` (~L598): scans UTC-date today/yesterday under scoped home.

## #M-4 evidence preamble — every claim you report MUST be tool-backed
| Claim | Required evidence (command + raw output) |
|---|---|
| "capture fix works" | run capture logic against the EXISTING rollout file above; show it extracts 14 calls incl. 4 verify_words — WITHOUT re-running codex |
| "tests pass" | `.venv/bin/pytest tests/agent_runtime/...` final `N passed` line raw |
| "lint clean" | `.venv/bin/ruff check scripts tests` final line raw |
| "no sibling instances" | the `grep`/`rg` command + its raw output |
| "commit landed" | `git log -1 --oneline` raw |
| "PR opened" | `gh pr view --json url` raw URL |

## Numbered steps
1. `git worktree add` (handled by `--worktree`). Branch off `origin/main`.
2. **Fix Part 1** — `_candidate_rollout_dirs`: include **local-date** today/yesterday dirs as well as UTC-date today/yesterday (deduped), all under the scoped `CODEX_HOME`. Use ±1 day around both UTC and local `now` to be robust to the midnight straddle in either direction.
3. **Fix Part 2** — `_check_rollout_liveness` (and any sibling capture/liveness helper): use the scoped `CODEX_HOME` (`self._codex_home_scope`), NOT `Path.home()/.codex`, and include local-date dirs.
4. **Sibling-failure sweep (REQUIRED — fix the class, not the instance):** `rg -n "datetime\.(now\(UTC\)|utcnow)|sessions/.*%Y|Path.home\(\).*codex"` across `scripts/agent_runtime/adapters/*.py` (esp. `cursor.py` — same rollout-scan pattern) and any rollout-tailing monitor code. Fix every place that assumes UTC date == on-disk session date. List what you found and what you fixed.
5. **Regression test** in `tests/agent_runtime/` (or the existing codex adapter test file): simulate a rollout written under the LOCAL-date dir while UTC date differs (midnight-straddle), assert `_candidate_rollout_dirs` includes it and the calls are captured. A synthetic 1-call rollout fixture is fine; assert non-empty extraction.
6. (OPTIONAL defense-in-depth — only if cheap) Part 3-minimal: a writer gate that fails `verify_words_missing` if a `*-tools` writer captured zero `mcp__sources__verify_words` calls. Codex already calls it, so this is a safety net, not the fix. Skip if it risks the time budget.
7. `.venv/bin/ruff check scripts tests` → clean.
8. `.venv/bin/pytest` on the affected adapter + any touched test modules → green.
9. Commit (conventional: `fix(codex-adapter): scan local-date rollout dirs so writer tool calls are captured`), trailer `X-Agent: codex/codex-rollout-capture-fix-20260529`, run `.venv/bin/python scripts/audit/lint_agent_trailer.py`.
10. `git push -u origin`, `gh pr create` (body: root cause = UTC-vs-local-date rollout discovery; the smoking-gun rollout path + the 14 captured calls; sibling sweep results; the one-line confirmation below). **Do NOT auto-merge.**

## One-line end-to-end confirmation (for the PR body)
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer codex-tools --use-generator --worktree; wt=$(ls -td .worktrees/builds/a1-my-morning-* | head -1); jq -e '[.[] | select((.namespace?=="mcp__sources__") or ((.name? // "")|startswith("mcp__sources__")))] | length > 0' "$wt/curriculum/l2-uk-en/a1/my-morning/writer_tool_calls.json"
```
