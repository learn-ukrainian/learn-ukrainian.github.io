# Codex dispatch brief — #1806 wiki/review.py codex MCP fail-fast (mirror PR #1802)

**Background:** PR #1802 added fail-fast pre-flight to `linear_pipeline._runtime_tool_config` — raises `LinearPipelineError` when a `-tools` writer requests MCP but resolves no servers. The wiki review path (`scripts/wiki/review.py:_tool_config_for`) has the same structural risk. Without this fix, a misconfigured wiki reviewer dispatches codex tool-less and codex hallucinates verification — exact failure mode #1798 was filed to prevent.

Read the full issue body via `gh issue view 1806` for the complete fix outline (includes pseudocode).

## Worktree

You start in `.worktrees/dispatch/codex/1806-wiki-review-mcp-fail-fast/` on branch `codex/1806-wiki-review-mcp-fail-fast`. Do NOT `cd` out.

## Files

- **Edit:** `scripts/wiki/review.py:255-264` — `_tool_config_for(agent, *, needs_mcp)`. Add `event_sink` parameter, emit `mcp_config_resolved`, raise on empty resolved_servers.
- **Reference (mirror):** `scripts/build/linear_pipeline.py:_runtime_tool_config` (the PR-#1802 pattern).
- **New error class:** define `WikiReviewError` in `scripts/wiki/review.py` if no equivalent exists. Or import `LinearPipelineError` if architecturally OK.
- **Tests:** add to `tests/test_mcp_init_observability.py` (parametrize over reviewer label) OR create `tests/test_wiki_review_mcp_init.py`.

## Numbered steps

1. Verify worktree.
2. Read `scripts/wiki/review.py` end-to-end + the relevant block in `linear_pipeline.py:_runtime_tool_config` (PR #1802 pattern).
3. Implement the fail-fast guard per the issue's pseudocode. Decision: where does `WikiReviewError` live and is it imported from `linear_pipeline` or new? Smallest-blast-radius decision.
4. Wire `event_sink` parameter through callers — find where `_tool_config_for` is called via `grep -n "_tool_config_for" scripts/wiki/`.
5. Add 2-3 tests:
   - `test_wiki_review_codex_emits_resolution_event` — happy path
   - `test_wiki_review_codex_raises_when_unconfigured` — fail-fast path
   - `test_wiki_review_claude_no_raise_when_unconfigured` — claude doesn't need MCP fail-fast (matches PR #1802 scoping).
6. Run targeted tests: `.venv/bin/pytest tests/test_mcp_init_observability.py tests/test_wiki_review*.py -v`.
7. Ruff.
8. Commit:
   ```
   fix(wiki): MCP fail-fast on codex reviewer dispatch (#1806)

   Mirrors PR #1802's writer-side guard for the wiki review path. When
   codex reviewer requests MCP servers but resolver returns none,
   raise hard rather than dispatching tool-less and getting
   hallucinated verification.

   Closes #1806
   Refs #1802 (the writer-side pattern), #1798 (original observability gap)
   ```
9. Push + PR. Do NOT auto-merge.

## Acceptance criteria (from issue)

- [ ] `_tool_config_for` raises hard error when codex agent requests MCP but resolver returns none.
- [ ] `mcp_config_resolved` event emitted on reviewer JSONL stream.
- [ ] Test fixture exercises the failure path.
- [ ] No regression on wiki reviews that DO have MCP wired correctly.

## What NOT to do

- Do NOT change `linear_pipeline._runtime_tool_config` — that one already has the guard.
- Do NOT broaden the fail-fast to claude/gemini reviewers without rechecking PR #1802's scoping decision (which only applies it to codex because Claude/Gemini have different MCP-load behavior).
- Do NOT enable auto-merge.
