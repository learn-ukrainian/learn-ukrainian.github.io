# PR #2266 adjustment — Codex UI pickup prompt

**Use this if the headless dispatch `pr-2266-adjustment-2026-05-25` fails / silence-times out / doesn't complete.**

Paste the block below into the Codex UI in `/Users/krisztiankoos/projects/learn-ukrainian/` (main worktree). The prompt is self-contained — no conversation context needed.

---

## PROMPT (paste this into Codex UI)

You are picking up an in-flight PR adjustment task. The full brief is at:

```
docs/dispatch-briefs/2026-05-25-pr-2266-adjustment-codex.md
```

**Read that brief first, end to end.** It is the authoritative spec.

### What's already in flight

A headless dispatch (task id `pr-2266-adjustment-2026-05-25`, model gpt-5.5 high) was fired at 2026-05-25T07:15Z. Its worktree is at `.worktrees/dispatch/codex/pr-2266-adjustment-2026-05-25/` (branch `codex/pr-2266-adjustment-2026-05-25`, branched from `origin/main` at `0014318188`). Before starting:

1. `cd .worktrees/dispatch/codex/pr-2266-adjustment-2026-05-25` and run `git log --oneline main..HEAD` to see what commits already exist.
2. Run `git status --short` to see what's staged or uncommitted.
3. Run `gh pr list --state open --search "pr-2266"` to see if any PR-A / PR-B PRs have already been opened by the dispatch.
4. Read the dispatch worktree's last commit message + diff to understand where the prior session stopped.

If the dispatch made partial progress, RESUME from where it left off. If it made no progress, start fresh in this same worktree (the branch is already created).

### Two pytest failures surfaced on PR #2266 after the dispatch started

These are not in the original brief but are part of PR-A scope:

```
FAILED tests/test_citation_resolve.py::test_page_range_and_second_page_label_do_not_pass
    - assert True is False

FAILED tests/test_agent_runtime_tool_calls.py::test_normalize_tool_calls_correlates_codex_function_call_output
    - AttributeError: 'list' object has no attribute 'startswith'
```

**Failure 1 (page-range test)**: This test enshrines the OLD behavior — "page ranges like `p.124-125` should NOT match". PR #2266 intentionally added page-range support to `scripts/build/citation_matcher.py`. The test is now stale. **FLIP IT** per the orchestrator skill's adapter-bug discipline rule: when a test enshrines a bug or obsolete contract, the fix is to update the test to assert the new (correct) behavior, not to bypass the test. Add a regression test that pins the NEW behavior (`p.124-125` DOES match a plan reference at `p.125`). Document the flip with a 1-line comment above the test referencing PR #2266.

**Failure 2 (tool_calls list/startswith)**: This is a REAL bug in `scripts/agent_runtime/tool_calls.py` introduced by PR #2266's changes. Some code path now passes a `list` value where a `str` is expected, and calls `.startswith()` on it. Find the call site, check the data shape that flows in, fix the conversion (or guard with `isinstance(x, str)` before calling), and verify with `pytest tests/test_agent_runtime_tool_calls.py -q`.

Both failures MUST be addressed in PR-A (the plumbing split), not in PR-B (the content split). PR-B should not change either of those files.

### Constraints

1. Two PRs, not one. PR-A = 9 plumbing + 7 tests + the two fixes above. PR-B = 2 content files (the b1 MDX + the b1 landing card unlock) with the Tab 4 metadata leak stripped per §3a of the brief.
2. PR #2266 stays OPEN until both replacements are merged. Close it ONLY after PR-A and PR-B are merged, with a comment linking both.
3. Conventional commits. No `--auto`, no `--admin`. The `review/review` Gemini Dispatch advisory failure is known-broken (per `memory/MEMORY.md` #M-0.5) and is NOT a merge blocker. Everything else MUST be green.
4. Per `#M-4` (deterministic over hallucination), include in each PR body the literal command + cwd + raw output for:
   - `.venv/bin/python -m pytest tests/ -q --no-header` (the final summary line)
   - `.venv/bin/ruff check scripts tests` (the final summary line)
   - `cd starlight && npm run build` (the final summary line — only required for PR-B)
   - `.venv/bin/python scripts/audit/lint_agent_trailer.py` (the final line)
5. PR-B body MUST include the result of:
   ```
   grep -c "chunk_id\|writer telemetry" starlight/src/content/docs/b1/adjectives-comparative.mdx
   ```
   That count MUST be `0` after your fixes. If it's nonzero, you missed a leak.
6. File the 3 follow-up issues named in §3a of the brief:
   - MDX assembler / writer template leaking pipeline metadata into Tab 4 (root cause)
   - `wiki_coverage_gate._activity_text` workbook+error-correction keyword bypass — generalize or document
   - Validate the new 3-line pre-emit audit contract works for `claude-tools` / `gemini-tools` / `deepseek-tools`

### Stop conditions (do NOT silently power through)

Stop and report (in chat or PR body comment) if any of these fire:

- The page-range test flip is non-trivial because the test contract isn't what I described above — show me the actual test body before changing it.
- The `'list'.startswith` bug fix would require >50 LOC or touches files outside `scripts/agent_runtime/tool_calls.py` and its direct callers — show me the call chain first.
- The Tab 4 metadata leak appears to be coming from a place the brief did not anticipate (not just MDX text but a YAML field or assembler template).
- Any of the 9 plumbing files in the brief is NOT actually in the diff of PR #2266 (verify before assuming).
- The blocking pytest failures persist after your fixes — do NOT open the PR yet; show me the failure first.

### When done

Reply with:
1. Both PR URLs (PR-A first, PR-B second).
2. The status check rollup for each (paste the `gh pr checks <N>` raw output).
3. The 3 follow-up issue URLs.
4. The grep count for the Tab 4 metadata leak (must be 0).
5. The comment URL you posted on #2266 closing it as superseded.

If you stop early per a stop condition, give me:
- The condition that fired (quote it verbatim).
- What you already changed (raw `git status --short` + `git log --oneline main..HEAD`).
- What you need from me before resuming.
