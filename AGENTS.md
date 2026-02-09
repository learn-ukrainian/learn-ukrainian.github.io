# AGENTS.md - Rules for AI Coding Agents

> This file is read by Jules, Gemini, and other AI agents working on this repository.
> For Claude-specific instructions, see `CLAUDE.md`.
> For Gemini-specific instructions, see `GEMINI.md`.

---

## MANDATORY PRE-SUBMIT CHECKLIST

**Before creating a PR, verify EVERY item. If ANY check fails, fix it BEFORE submitting.**

- [ ] `.python-version` is unchanged (must be `3.12.8`)
- [ ] `.yamllint` is unchanged (zero modifications)
- [ ] `.markdownlint.json` is unchanged (zero modifications)
- [ ] No `status/*.json` files in the diff
- [ ] No `audit/*-review.md` files in the diff
- [ ] No `review/*-review.md` files in the diff
- [ ] No `sys.executable` anywhere in code (use `.venv/bin/python`)
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened (e.g., `is True` → `isinstance(..., bool)`)
- [ ] Every changed file is directly related to the task
- [ ] Total files changed < 20 (if more, you likely included artifacts)
- [ ] Code runs without `NameError`, `KeyError`, or `ImportError`

**If you cannot check every box, your PR WILL be rejected.**

---

## Non-Negotiable Rules

These rules are ABSOLUTE. Violating ANY of them results in immediate PR rejection.
**100% of recent PRs violated these rules. Read carefully.**

### 1. NEVER Change `.python-version`

The file `.python-version` is set to `3.12.8`. This version is compiled via pyenv with `--enable-loadable-sqlite-extensions` for sqlite-vec support. Changing it to 3.12.12 or any other version breaks every developer's environment.

**Do not touch this file. Not even to "upgrade" it.**

### 2. NEVER Modify Linter Configs

`.markdownlint.json` and `.yamllint` contain intentional style rules.

**If your code fails linting:**
- **Fix the source files**, not the linter config
- Do NOT disable rules to make CI pass
- Do NOT set rules to `false` or `disable`
- Do NOT add `key-duplicates: disable` (duplicate YAML keys silently overwrite data)

**This is the #1 reason PRs get rejected.** Every single PR in the last batch gutted linter configs. "Fix source, not symptoms" is a core project principle.

### 3. NEVER Use `sys.executable`

```bash
# CORRECT — in shell commands
.venv/bin/python scripts/audit_module.py path/to/module.md

# CORRECT — in Python subprocess calls
subprocess.run(['.venv/bin/python', 'scripts/audit_module.py', path])

# WRONG — uses system Python, missing deps
python3 scripts/audit_module.py path/to/module.md
subprocess.run([sys.executable, 'scripts/audit_module.py', path])
```

`sys.executable` may point to the system Python or a different interpreter that lacks sqlite-vec and other venv dependencies. **Always use `.venv/bin/python` explicitly.**

### 4. NEVER Include Auto-Generated Files in Code PRs

These files are auto-generated and MUST NOT appear in PRs that change code/scripts:

- `curriculum/l2-uk-en/**/status/*.json` — audit cache files
- `curriculum/l2-uk-en/**/audit/*-review.md` — auto-generated reviews
- `curriculum/l2-uk-en/**/review/*-review.md` — review files
- `docs/*-STATUS.md` — level status reports

**Why this is critical:**
- Creates massive diffs (one PR had 296 artifact files out of 301 total)
- Overwrites hand-crafted reviews with generic machine output
- Introduces data regressions (e.g., `"plan": null` in status JSONs)
- Makes code review impossible (real changes buried in noise)

**Rule of thumb:** If your PR touches more than 20 files, you almost certainly included artifacts. Check your diff.

### 5. NEVER Weaken Tests

- Do NOT add `@pytest.mark.skip` with empty `pass` bodies
- Do NOT change `assert result['passed'] is True` to `assert isinstance(result['passed'], bool)`
- Do NOT stub imports with `try/except` that silently return empty results
- Do NOT comment out assertions
- Do NOT use double `@pytest.mark.skip` decorators (copy-paste error)

If tests fail, **fix the underlying code** or properly rewrite the tests. Dead tests are worse than no tests.

### 6. NEVER Fabricate Documentation

Do NOT invent:
- Error codes that don't exist in the codebase
- Phases/workflows that don't exist
- Screenshots or assets that don't exist
- API endpoints that don't exist
- Review documents at the repo root (e.g., `CODEBASE_QUALITY_REVIEW.md`)

**Read the actual source code first.** Reference real function names, real file paths, real workflows.

### 7. NEVER Delete Files Without Explicit Instructions

Do not remove scripts, utilities, or debug tools unless the task specifically asks for it. Files that exist in the repo exist for a reason. One failed session deleted 21 scripts — all were needed.

### 8. ALWAYS Test Your Code Before Submitting

Run the scripts you modified. Check for:
- `NameError` — variables referenced but not defined in scope
- `KeyError` — dictionary keys assumed but not present
- `ImportError` — modules imported but not installed
- Variable scoping bugs in multiprocessing/threading code
- `lru_cache` on functions that return mutable data (stale results)
- Temp files created with `delete=False` but never cleaned up

### 9. Scope Your PRs

One PR = one concern. Do NOT:
- Change linter configs in a "performance optimization" PR
- Change `.python-version` in a "test suite" PR
- Delete files in a "fix docs" PR
- Add unrelated CI changes in a "monitoring" PR
- Regenerate all audit/status files in a "code change" PR

If you find something unrelated that needs fixing, create a separate issue.

### 10. NEVER Use Container Paths

This project runs **locally with pyenv**, NOT in Docker. Do not use:
- `/app/curriculum/...` — use relative paths or real local paths
- `localhost:8765` — use relative URLs (`/api/...`)

---

## Project Architecture

```
curriculum/l2-uk-en/
├── plans/{level}/{slug}.yaml     # SOURCE OF TRUTH (immutable)
├── {level}/meta/{slug}.yaml      # Build config (mutable)
├── {level}/{num}-{slug}.md       # Lesson content
├── {level}/activities/{slug}.yaml # Activities (bare list at root!)
├── {level}/vocabulary/{slug}.yaml # Vocabulary
├── {level}/status/{slug}.json    # AUTO-GENERATED — never include in PRs
└── {level}/audit/{slug}-review.md # AUTO-GENERATED — never include in PRs
```

**Key facts:**
- Activity YAML must be a bare list at root, NOT wrapped in `activities:` key
- Word targets in plans are MINIMUMS, not maximums
- Dependencies: `pyproject.toml` (NOT `requirements.txt` — it doesn't exist)
- Repo: `learn-ukrainian/learn-ukrainian.github.io`
- Python: pyenv 3.12.8 (NOT 3.10, NOT 3.12.12)
- All documentation goes in `docs/`, not repo root
- Only `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `README.md` belong at root

## Common Anti-Patterns (All Seen in Recent PRs)

| Anti-Pattern | Frequency | What to Do Instead |
|---|---|---|
| Disable/gut `.yamllint` rules | 100% of PRs | Fix the source files that fail linting |
| Disable/gut `.markdownlint.json` rules | 80% of PRs | Fix the markdown files |
| Change `.python-version` to 3.12.12 | 60% of PRs | Don't. It must stay 3.12.8 |
| Include 50-300 regenerated artifacts | 60% of PRs | Only include files you actually changed |
| Use `sys.executable` in subprocess | 40% of PRs | Use `.venv/bin/python` |
| Skip tests with `@skip` + `pass` | 40% of PRs | Fix the code or rewrite the test |
| Ship code with `NameError` at runtime | 40% of PRs | Run your code before submitting |
| Scope creep (unrelated changes) | 80% of PRs | One PR = one concern |
| Use `/app/` container paths | 20% of PRs | Use real local paths or relative paths |
| Reference `requirements.txt` | seen | Use `pyproject.toml` |
| Delete existing scripts/files | seen | Don't delete without explicit instructions |
| Create root-level doc files | seen | Put documentation in `docs/` |
