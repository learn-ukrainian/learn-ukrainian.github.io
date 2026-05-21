# Code Review Checklist

Run every check in order. Report findings at the end. Fix anything fixable before reporting.

---

## Step 1: Identify changed files

```
git diff --name-only HEAD
git diff --cached --name-only
git status --short
```

If the user specified files, use those instead. Filter to `.py`, `.ts`, `.tsx`, `.js` files only.

---

## Step 2: Ruff lint (Python files only)

Run ruff on every changed `.py` file:

```bash
.venv/bin/ruff check --fix {files}
```

If ruff finds unfixable issues, report them. If `--fix` resolves them, note what was fixed.

---

## Step 3: Project-specific checks

For each changed Python file, check for:

### 3a. Model constants

- Any hardcoded model strings (`"claude-opus-4-6"`, `"claude-sonnet-4-6"`, `"gemini-3.1-pro-preview"`, `"gemini-3-flash-preview"`)?
- Should they come from `batch_gemini_config.py` instead?

### 3b. Import hygiene

- Any `import re` or `import json` inside a function when already imported at module level?
- Any unused imports?

### 3c. SQLite connection management

- Any `sqlite3.connect()` calls that open a new connection per invocation instead of reusing?
- Any connections not closed in a `finally` block or context manager?

### 3d. Silent failures

- Any bare `except: pass` or `except Exception: pass` that swallows errors?
- Any functions that return `None` on failure without logging?

### 3e. Dead code

- Any functions defined but never called? (Check with grep for the function name across the codebase)
- Any unreachable branches (code after `return`)?

### 3f. Type hints

- Do new/changed functions have return type annotations?
- Do function parameters have type annotations?

### 3g. Test coverage

- Does every new/changed function have a corresponding test?
- If not, flag which functions need tests.

---

## Step 4: Simplify pass

For each changed file, check for:
- Duplicated logic that could be extracted to a shared function
- Overly complex conditions that could be simplified
- Functions longer than 50 lines that should be split
- Magic numbers that should be named constants

---

## Step 5: Cross-agent review (when available)

If Gemini is available, send the diff for adversarial review:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Code review this diff. Find bugs, logic errors, missed edge cases, and style issues." \
  --task-id code-review --model gemini-3.1-pro-preview
```

**If Gemini is unavailable (currently down)**: Skip this step. Note "Gemini review skipped (service unavailable)" in the report.

---

## Step 5b: Challenge round (anti-false-positive)

Reviewer findings include false positives — the writer's choice was correct and the reviewer pattern-matched on a surface signal. Auto-applying every finding produces churn and sometimes regresses the diff.

Send the FINDINGS LIST from Step 5 to a **different** agent (Codex, since Gemini was the reviewer) for an adversarial pass that argues *for* the writer:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex - \
  --task-id code-review-challenge --to-model gpt-5.5 <<'EOF'
Below is a code diff and a list of issues raised by a reviewer agent.
Your job: identify which findings are LIKELY FALSE POSITIVES where the
writer's choice was correct, and which are real bugs. Be skeptical of
the reviewer. Pattern-match on these false-positive shapes:

- "missing tests" when the function is trivially a thin wrapper or pure config
- "silent failure" when the bare except is intentional and documented inline
- "magic number" when the number is a domain constant (HTTP status, port, etc.)
- "dead code" when grep missed dynamic import / re-export / test fixture
- "type hints missing" when the function is `__init__` or matches a typing.Protocol

For each finding emit ONE LINE in this exact format:

  KEEP <finding_id>: <one-sentence rationale>
  DROP <finding_id>: <one-sentence why it's a false positive>
  EVIDENCE_NEEDED <finding_id>: <what to check before deciding>

Do not invent new findings. Only adjudicate the ones supplied.

---DIFF---
{paste git diff output here}
---FINDINGS---
{paste numbered finding list from Step 5 here}
EOF
```

**Filter rule for Step 6 application:**
- `KEEP` findings → apply the fix
- `DROP` findings → skip silently (do not apply, do not surface to user unless they ask)
- `EVIDENCE_NEEDED` findings → run the suggested check; if it confirms the bug, apply; if not, drop

**If Codex is unavailable**: Skip this step. Note "Challenge round skipped (Codex unavailable)" in the report; apply Gemini's findings as-is.

**Cross-model invariant**: the challenger MUST be a different model family from the reviewer (per `SELF_REVIEW_DETECTED` audit gate intent). If Gemini reviewed, Codex challenges. If Codex reviewed (rare for this skill), DeepSeek-pro challenges.

---

## Step 6: Run affected tests

```bash
.venv/bin/pytest {relevant_test_files} -v --tb=short
```

Find relevant tests by matching changed file names to test files:
- `scripts/build/v7_build.py` → `tests/test_v7_writer_dispatch.py`
- `scripts/audit/core.py` → `tests/test_audit_core.py`
- etc.

If no matching test file exists, flag it.

---

## Step 7: Report

Output a structured report:

```
## Code Review Report

### Files reviewed
- {file1} ({lines_changed} lines changed)
- {file2} ...

### Ruff
{ruff findings or "Clean"}

### Project checks
{findings per category, or "Clean" per category}

### Simplify
{suggestions or "No issues"}

### Cross-agent review
{Gemini findings or "Skipped (unavailable)"}

### Challenge round
{N findings KEPT, M findings DROPPED, K need evidence — or "Skipped (Codex unavailable)"}

### Tests
{test results or "No matching tests found — NEEDS TESTS: {functions}"}

### Summary
{X issues found: Y critical, Z major, W minor}
{list of fixes applied}
{list of issues remaining}
```
