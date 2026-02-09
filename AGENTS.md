# AGENTS.md - Rules for AI Coding Agents

> This file is read by Jules, Gemini, and other AI agents working on this repository.
> For Claude-specific instructions, see `CLAUDE.md`.
> For Gemini-specific instructions, see `GEMINI.md`.

## Non-Negotiable Rules

These rules are ABSOLUTE. Violating them will result in PR rejection.

### 1. NEVER Change `.python-version`

The file `.python-version` is set to `3.12.8`. This version is compiled via pyenv with `--enable-loadable-sqlite-extensions` for sqlite-vec support. Changing it breaks every developer's environment. **Do not touch this file.**

### 2. NEVER Gut Linter Configs

`.markdownlint.json` and `.yamllint` contain intentional style rules. If your code fails linting:

- **Fix the code**, not the linter config
- Do NOT disable rules to make CI pass
- Do NOT set rules to `false` or `disable`
- If a specific rule is genuinely wrong for this project, explain why in the PR description

**This is the #1 reason PRs get rejected.** "Fix source, not symptoms" is a core project principle.

### 3. ALWAYS Use `.venv/bin/python`

```bash
# CORRECT
.venv/bin/python scripts/audit_module.py path/to/module.md

# WRONG - missing venv dependencies, wrong Python binary
python3 scripts/audit_module.py path/to/module.md
python scripts/audit_module.py path/to/module.md
sys.executable  # in Python code - may point to wrong interpreter
```

The venv is created from the pyenv Python 3.12.8 with sqlite extensions. Using `sys.executable` or bare `python3` may use a different interpreter that lacks required dependencies.

### 4. NEVER Fabricate Documentation

Do NOT invent:
- Error codes that don't exist in the codebase
- Phases/workflows that don't exist
- Screenshots or assets that don't exist
- API endpoints that don't exist

If documenting something, **read the actual source code first**. Reference real function names, real file paths, real workflows.

### 5. NEVER Weaken Tests

- Do NOT skip tests with empty `pass` bodies — delete them or fix them
- Do NOT change strict equality assertions to subset checks
- Do NOT stub imports with try/except that silently return empty results
- Do NOT change `assert result['passed'] is True` to `assert isinstance(result['passed'], bool)`

If tests fail, fix the underlying code or properly rewrite the tests. Dead tests with `@skip` and `pass` are worse than no tests.

### 6. NEVER Include Regenerated Artifacts in Code PRs

Audit review files (`audit/*-review.md`) and status files (`status/*.json`) are auto-generated. Do NOT include them in PRs that change code/scripts. They create massive diffs, can overwrite hand-crafted reviews, and introduce data regressions (e.g., `plan: null`).

### 7. Scope Your PRs

One PR = one concern. Do NOT:
- Change linter configs in a "performance optimization" PR
- Change `.python-version` in a "test suite" PR
- Delete documentation files in a "fix docs" PR
- Add unrelated CI changes in a "monitoring" PR

If you find something unrelated that needs fixing, create a separate issue.

## Project Architecture

```
curriculum/l2-uk-en/
├── plans/{level}/{slug}.yaml     # SOURCE OF TRUTH (immutable)
├── {level}/meta/{slug}.yaml      # Build config (mutable)
├── {level}/{num}-{slug}.md       # Lesson content
├── {level}/activities/{slug}.yaml # Activities (bare list at root!)
├── {level}/vocabulary/{slug}.yaml # Vocabulary
├── {level}/status/{slug}.json    # Auto-generated audit cache
└── {level}/audit/{slug}-review.md # Auto-generated review
```

**Key facts:**
- Activity YAML must be a bare list at root, NOT wrapped in `activities:` key
- Word targets in plans are MINIMUMS, not maximums
- Dependencies: `pyproject.toml` (NOT `requirements.txt` — it doesn't exist)
- Repo: `learn-ukrainian/learn-ukrainian.github.io`
- Python: pyenv 3.12.8 (NOT 3.10, NOT 3.12.12)

## Common Anti-Patterns to Avoid

| Anti-Pattern | What to Do Instead |
|---|---|
| Disable lint rules to pass CI | Fix the files that fail linting |
| Skip failing tests | Fix the code or properly rewrite tests |
| Use `sys.executable` | Use `.venv/bin/python` |
| Include 50+ regenerated files | Only include files you actually changed |
| Fabricate docs from imagination | Read source code and document what exists |
| Change `.python-version` | Don't. Ever. |
| Reference `requirements.txt` | Use `pyproject.toml` |
| Use `/app/` container paths | Use real local paths or relative paths |
| Hardcode `localhost` URLs | Use relative URLs (`/api/...`) |
| Create `bin/` duplicates of scripts | Use one canonical location |
