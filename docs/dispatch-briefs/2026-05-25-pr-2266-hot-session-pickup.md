# Hot-session pickup prompt for codex UI

**Paste the block below into the running codex UI session.** Codex has context — this is short on purpose.

---

## PROMPT

The headless dispatch you were running (`pr-2266-adjustment-2026-05-25`) died at the silence-timeout mark with no commits, but your uncommitted work survives in two worktrees. Pick it up from there.

### Where your work is

Two worktrees on disk, both at base SHA `0014318188`, branches already created, files already edited but **not committed**:

**1. `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/2266-v7-plumbing`** (branch `codex/2266-v7-plumbing`) — PR-A plumbing split. 20 modified files including all 9 plumbing files from the brief + all 7 tests + one new file `scripts/audit/check_russicisms.py`. Note: `starlight/src/content/docs/a1/index.mdx` and `scripts/build/phases/linear-write-grok.md` are also modified — verify they belong in PR-A scope, drop the edit if not.

**2. `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/2266-b1-adjectives-content`** (branch `codex/2266-b1-adjectives-content`) — PR-B content split. 2 files: `starlight/src/content/docs/b1/adjectives-comparative.mdx` (new) + `starlight/src/content/docs/b1/index.mdx` (modified).

### What I need from you

For each worktree, in this order:

1. **Verify the diff is what we want.** `cd` in, run `git diff --stat` then `git diff` for each file. Sanity-check:
   - PR-A: the 9 plumbing files + 7 tests match the brief's scope. The two pytest failures are addressed: `tests/test_citation_resolve.py::test_page_range_and_second_page_label_do_not_pass` is FLIPPED (asserts new page-range-matches behavior with a comment referencing PR #2266); `tests/test_agent_runtime_tool_calls.py::test_normalize_tool_calls_correlates_codex_function_call_output` is GREEN because the real bug in `scripts/agent_runtime/tool_calls.py` (a list being passed to `.startswith()`) is fixed. The four out-of-brief files (`linear-write-grok.md`, `starlight/.../a1/index.mdx`, `check_russicisms.py`) either belong here for a real reason or get reverted before commit.
   - PR-B: `adjectives-comparative.mdx` has NO `chunk_id` or `writer telemetry` strings (`grep -c "chunk_id\|writer telemetry" starlight/src/content/docs/b1/adjectives-comparative.mdx` returns `0`). The Tab 4 (Ресурси) bullets are clean Ukrainian descriptions, not pipeline metadata.

2. **Run verification per #M-4** in EACH worktree:
   - `.venv/bin/python -m pytest tests/ -q --no-header` — must show all-green summary
   - `.venv/bin/ruff check scripts tests` — must show "All checks passed!"
   - PR-B only: `cd starlight && npm run build` — must build successfully
   - PR-A only: `.venv/bin/python scripts/audit/lint_agent_trailer.py` — must pass

3. **Commit + push + open the PRs.** Conventional commits. PR-A first:
   ```
   fix(v7): pre-emit audit tightening + reviewer-override + citation page-range + wiki_coverage compact-pipe parse

   - linear-write.md: add bad_form_audit + activity_split_audit pre-emit lines
   - v7_build.py: _writer_preemit_audit_context() pipes audit into reviewer; reviewer_override threaded
   - citation_matcher.py: page_end optional, range-aware match
   - wiki_coverage_gate.py: compact pipe parse; <state decision on workbook+error-correction>
   - tool_calls.py: fix list-vs-str in normalize_tool_calls path (closes flake on test_normalize_tool_calls_correlates_codex_function_call_output)
   - tests: cover all changes incl. flipped test_page_range_and_second_page_label_do_not_pass + new range regression
   ```

   Then PR-B:
   ```
   feat(b1): publish adjectives comparative module

   - starlight b1/adjectives-comparative.mdx: 4-tab V7 shape, 41 vocab, 11 activities
   - b1/index.mdx: module 44 landing card marked complete
   - Tab 4 metadata leak stripped (chunk_id / writer telemetry strings removed)
   - depends on #<PR-A>
   ```

4. **Both PR bodies** must paste the raw output of each verification command + the `grep -c` result for the Tab 4 leak (must be 0). Per `#M-4`, command + cwd + raw final-summary line.

5. **Close PR #2266** with a comment linking PR-A and PR-B as the replacement: `gh pr close 2266 --comment "Superseded by #<PR-A> + #<PR-B>."`

6. **File 3 follow-up issues** named in §3a of the brief (`docs/dispatch-briefs/2026-05-25-pr-2266-adjustment-codex.md` §3a + §2a + §2b):
   - "mdx-assembler: writer telemetry / chunk_id strings leaking into Ресурси tab"
   - "wiki_coverage_gate._activity_text: workbook+error-correction keyword bypass — generalize or document"
   - "validate new 3-line pre-emit audit contract for claude-tools / gemini-tools / deepseek-tools"

7. **No `--admin`, no `--auto`.** `review/review` Gemini Dispatch advisory failure is the only acceptable red check (known broken per `memory/MEMORY.md` #M-0.5). Everything else MUST be green before you reply done.

### Stop conditions

Stop and ask me (in chat) if:
- The four out-of-brief files in PR-A worktree (linear-write-grok.md, a1/index.mdx, check_russicisms.py, plus any I missed) don't have a clear reason to be in PR-A scope.
- Either pytest failure persists after the fix you already wrote.
- The Tab 4 grep returns nonzero in `adjectives-comparative.mdx`.
- Any verification command fails for a reason that needs > 30 LOC of additional fix.

### When done

Reply with: both PR URLs, `gh pr checks <N>` raw output for each, the 3 follow-up issue URLs, the Tab 4 grep count (must be `0`), and the close-comment URL on #2266.

Full original brief if you need the WHY behind any of this: `docs/dispatch-briefs/2026-05-25-pr-2266-adjustment-codex.md`.
