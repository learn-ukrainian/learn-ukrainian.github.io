# Dispatch brief — Issue #2239: codex rollout binding broken (P1)

**Agent:** codex (it's the codex adapter, codex understands its own rollout format best) — fallback claude headless if codex regression makes it untrustworthy
**Task ID:** `issue-2239-codex-rollout-binding-fix-2026-05-23`
**Worktree:** auto via `--worktree`
**Mode:** `danger`
**Effort:** `xhigh`
**Base SHA:** post-PR-B merge (`c363726b44` or newer)
**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2239
**Authority:** issue body + handoff `docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md` carry-over F2.

## #M-4 preamble

Every verifiable claim MUST be tool-backed (command + cwd + raw output). Required:

| Claim | Evidence |
|---|---|
| Diff inspection captured | `grep -n` output of pre/post payload bytes |
| Tests pass | `.venv/bin/python -m pytest tests/agent_runtime/test_codex_adapter.py tests/agent_runtime/test_codex_rollout_match.py -v` + raw final line |
| Lint clean | `.venv/bin/ruff check scripts/agent_runtime/adapters/codex.py tests/agent_runtime/test_codex_rollout_match.py` + raw final line |
| Commit landed | `git log -1 --oneline` raw |
| PR opened | `gh pr view --json url --jq .url` raw URL |

## Context — what is broken

V7 codex-tools writer builds work end-to-end EXCEPT for one fail point. The codex CLI emits a rollout `sessions/YYYY/MM/DD/rollout-*.jsonl` with all tool calls (48 valid `mcp__sources__*` invocations confirmed on the a1-my-morning-20260522-223407 build). The post-run code at `scripts/agent_runtime/adapters/codex.py::_select_rollout_for_plan` calls `_rollout_matches_plan` to bind the rollout to this invocation. The match returns False on every candidate rollout, so the adapter falls through to None, `writer_tool_calls.json` writes empty `[]`, and `mcp_tools_never_invoked` HARD-fails the build.

**Pre-PR-#2233:** the rollout was selected by file-system snapshot (newest after `build_invocation` start). Worked but unsafe under concurrent codex execs.

**PR #2233:** added byte-exact payload match as the verification step — only bind the rollout if its user_message matches `plan.stdin_payload` verbatim. Concurrency-safe but breaks because the byte comparison rejects valid matches.

## Hypothesis

The rollout's stored user_message has been transformed by the codex CLI before storage:
- Possible: line-ending normalization (CRLF → LF)
- Possible: trailing-newline addition or removal
- Possible: BOM insertion / Unicode normalization (NFC vs NFD)
- Possible: leading whitespace insertion (e.g. codex adds a wrapper line)

The byte-comparison at `scripts/agent_runtime/adapters/codex.py:812` and `:829` rejects ANY of these. We need either normalization-on-both-sides OR fingerprint-based matching.

## Steps — execute in order

### 1. Worktree setup (auto-created at `.worktrees/dispatch/codex/issue-2239-codex-rollout-binding-fix-2026-05-23/`)

```bash
git status --short  # expect empty
git log -1 --oneline  # expect c363726b44 (PR-B merged) or newer
```

### 2. Reproduce the failure under a diagnostic capture

Add a one-shot diagnostic at `scripts/agent_runtime/adapters/codex.py::_rollout_matches_plan` that, on every match attempt where the loop runs to end without returning True, dumps a comparison report to `/tmp/codex_rollout_mismatch_report.txt`:

```python
# Diagnostic — remove after #2239 fix lands.
def _rollout_matches_plan(self, rollout_path: Path, plan: InvocationPlan) -> bool:
    expected = (plan.stdin_payload or "").rstrip()
    if not expected:
        return True

    # ... existing loop ...

    # If we reach here, no match. Diagnostic dump.
    try:
        import os
        with open("/tmp/codex_rollout_mismatch_report.txt", "a", encoding="utf-8") as report:
            report.write(f"\n=== {rollout_path} ===\n")
            report.write(f"expected_len={len(expected)} expected_first200={expected[:200]!r}\n")
            report.write(f"expected_last200={expected[-200:]!r}\n")
            # ... scan rollout once more and dump every user_message ...
    except Exception:
        pass

    return False
```

Run a fresh codex-tools build to capture the report:

```bash
# venv symlinked
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer codex-tools --effort xhigh --worktree 2>&1 | grep --line-buffered '^{"event"' | tee /tmp/codex_build.jsonl
```

Wait for `module_failed` event (or `mcp_tools_never_invoked` gate fail).

Read `/tmp/codex_rollout_mismatch_report.txt`. Identify the difference:
- Length match but content differs → encoding/whitespace issue
- Length differs by small N → codex adds a wrapper of N chars
- Length differs by 50%+ → entire payload structure differs

### 3. Implement the fix

Based on the diagnostic, the fix is ONE of:

**Path A — normalize both sides:**
```python
def _normalize_for_match(s: str) -> str:
    """Normalize a payload string for byte-comparison.

    Codex CLI may add/strip trailing newlines, normalize line endings, or
    perform Unicode normalization. Apply the same normalizations on both
    sides before equality check.
    """
    import unicodedata
    # NFC normalization, CRLF → LF, strip trailing whitespace, collapse trailing newlines
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.rstrip()
    return s

# Use in _rollout_matches_plan:
expected = _normalize_for_match(plan.stdin_payload or "")
# ... later ...
if payload["message"] and _normalize_for_match(payload["message"]) == expected:
    return True
```

**Path B — suffix match (if codex adds prefix wrapper):**
```python
# If codex adds a wrapper prefix, the writer prompt content is at the END
# of the user_message. Match by suffix.
def _matches_by_suffix(rollout_msg: str, expected: str) -> bool:
    """Match by suffix when codex may wrap the payload with a prefix.

    Returns True if rollout_msg ends with expected (after normalization).
    """
    rollout_norm = _normalize_for_match(rollout_msg)
    expected_norm = _normalize_for_match(expected)
    return rollout_norm.endswith(expected_norm)
```

**Path C — fingerprint match (most robust, last resort):**
```python
import hashlib
def _payload_fingerprint(s: str, last_n: int = 4096) -> str:
    """Stable fingerprint: SHA256 of the last N chars (post-normalization)."""
    return hashlib.sha256(_normalize_for_match(s)[-last_n:].encode("utf-8")).hexdigest()

# Use:
if _payload_fingerprint(payload["message"]) == _payload_fingerprint(expected):
    return True
```

Recommendation order: try **Path A** first (cheapest, lowest risk). If diagnostic shows a wrapper prefix, escalate to **Path A + Path B** combined. Only use **Path C** if A+B both fail.

### 4. Remove the diagnostic block

Once the fix is verified, remove the `/tmp/codex_rollout_mismatch_report.txt` dump from `_rollout_matches_plan`. Production code does not write to `/tmp`.

### 5. Tests

**File:** `tests/agent_runtime/test_codex_rollout_match.py` (new — or extend existing test if one is present)

```python
"""Regression tests for codex rollout binding (#2239)."""

import json
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.codex import CodexAdapter, InvocationPlan


def _write_rollout(tmp_path: Path, user_message: str) -> Path:
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text(
        json.dumps(
            {
                "type": "event_msg",
                "payload": {"type": "user_message", "message": user_message},
            }
        )
        + "\n"
    )
    return rollout


def test_rollout_matches_with_trailing_newline(tmp_path: Path) -> None:
    """Codex CLI adds/strips trailing newline; match should still succeed."""
    adapter = CodexAdapter(config={})  # adjust constructor signature as needed
    plan = InvocationPlan(stdin_payload="hello world", ...)  # adjust kwargs
    rollout = _write_rollout(tmp_path, "hello world\n")
    assert adapter._rollout_matches_plan(rollout, plan) is True


def test_rollout_matches_with_crlf_normalization(tmp_path: Path) -> None:
    """CRLF in rollout matches LF in plan."""
    adapter = CodexAdapter(config={})
    plan = InvocationPlan(stdin_payload="line1\nline2\nline3", ...)
    rollout = _write_rollout(tmp_path, "line1\r\nline2\r\nline3\r\n")
    assert adapter._rollout_matches_plan(rollout, plan) is True


def test_rollout_rejects_unrelated_message(tmp_path: Path) -> None:
    """Different content should still reject."""
    adapter = CodexAdapter(config={})
    plan = InvocationPlan(stdin_payload="hello", ...)
    rollout = _write_rollout(tmp_path, "goodbye")
    assert adapter._rollout_matches_plan(rollout, plan) is False


def test_rollout_matches_response_item_shape(tmp_path: Path) -> None:
    """response_item events with content-list shape also match."""
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text(
        json.dumps({
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"text": "the prompt body"}],
            },
        }) + "\n"
    )
    adapter = CodexAdapter(config={})
    plan = InvocationPlan(stdin_payload="the prompt body", ...)
    assert adapter._rollout_matches_plan(rollout, plan) is True
```

Adjust `CodexAdapter` / `InvocationPlan` constructor args per the actual class signatures.

### 6. Run focused tests + relevant regression

```bash
# venv symlinked
.venv/bin/python -m pytest tests/agent_runtime/test_codex_rollout_match.py tests/agent_runtime/test_codex_adapter.py -v --timeout=120
```

Followed by:

```bash
# venv symlinked
.venv/bin/python -m pytest tests/agent_runtime/ -v --timeout=120 2>&1 | tail -30
```

### 7. Re-run the codex-tools build to validate end-to-end

```bash
# venv symlinked
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer codex-tools --effort xhigh --worktree 2>&1 | grep --line-buffered '^{"event"' | tee /tmp/codex_build_postfix.jsonl
```

Verify:
- `module_done` event appears (not `module_failed`)
- `writer_tool_calls.json` in the build's module_dir is NOT empty `[]`
- `mcp_tools_never_invoked` does NOT fail

### 8. Lint + commit + push + PR

```bash
.venv/bin/ruff check scripts/agent_runtime/adapters/codex.py tests/agent_runtime/test_codex_rollout_match.py
git add scripts/agent_runtime/adapters/codex.py tests/agent_runtime/test_codex_rollout_match.py
git commit -m "$(cat <<'EOF'
fix(codex-adapter): normalize payload before rollout match (#2239)

The byte-exact equality check in _rollout_matches_plan rejected valid
rollouts because Codex CLI normalized line endings / Unicode / trailing
newlines on storage. The actual writer prompt (208KB with 48 valid
mcp__sources__* tool calls) was present in the rollout but the matcher
returned False on every candidate.

Fix: apply NFC + CRLF→LF + trailing-whitespace normalization on BOTH
sides before equality comparison. Preserves the concurrency-safety of
PR #2233 (we still verify against payload content, not just snapshot
ordering) but tolerates codex's storage-side transformations.

Empirical validation: re-ran a1/my-morning codex-tools build; rollout
binds; writer_tool_calls.json captures the 48 mcp__sources__* calls;
mcp_tools_never_invoked passes.

Unblocks codex-tools as a viable V7 writer (specifically for seminars,
where it's the only writer that invokes query_ulif + query_pravopys +
search_heritage per the 2026-05-13 corpus matrix).

Fixes #2239.
Builds on #2230, #2232, #2233.

Co-Authored-By: Codex CLI <noreply@anthropic.com>
EOF
)"
git push -u origin HEAD
gh pr create --title "fix(codex-adapter): normalize payload before rollout match (#2239)" --body "..."
```

Use the issue body for the PR description. Surface the PR URL.

## Acceptance criteria

- Diagnostic captured + classified (Path A / B / C decision documented in PR body)
- Tests cover trailing-newline, CRLF normalization, response_item shape, and unrelated-rejection
- End-to-end codex-tools build succeeds (`writer_tool_calls.json` non-empty)
- Lint clean
- PR opened with URL surfaced

## Stay in scope

Do NOT touch:
- `scripts/build/v7_build.py` or `scripts/build/linear_pipeline.py` (the bug is in the adapter, not the pipeline)
- The Codex CLI integration anywhere outside `_rollout_matches_plan`
- Other writers (claude-tools, gemini-tools, deepseek-tools)
- Any unrelated test files

If something else seems broken: mention in PR body as a follow-up, do not fix here.
