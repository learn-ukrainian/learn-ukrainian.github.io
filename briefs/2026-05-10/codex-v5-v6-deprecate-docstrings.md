# Codex brief — v5/v6 deprecation docstrings

**Issue:** N/A (orchestrator-driven, follow-up to v6→V7 sweep `codex/v6-v7-doc-sweep`).
**Task ID:** `codex-v5-v6-deprecate-docstrings`
**Mode:** `--mode danger --worktree`
**Base:** `origin/main`

## Worktree

```
git worktree add -b codex-v5-v6-deprecate-docstrings .worktrees/codex-v5-v6-deprecate origin/main
cd .worktrees/codex-v5-v6-deprecate
```

## Context

User stated 2026-05-10: V7 is the only build pipeline. v5/v6 are obsolete and never going back. Their files remain on disk (forensic only), but their TOP-OF-FILE DOCSTRINGS still claim live status (current-tense, no obsolete marker). graphify and other LLM tooling read those docstrings and conclude v6 is "the primary entry point for modern module builds." Six lines of edits kill that signal.

## What to change (exact edits)

### `scripts/build/v6_build.py` — replace lines 1-7 (current docstring) with:

```python
#!/usr/bin/env python3
"""V6 Pipeline Build — OBSOLETE.

V6 was retired on 2026-05-10. Use ``scripts/build/v7_build.py`` (which drives
``scripts/build/linear_pipeline.py``) for all new builds. This file is kept
on disk for forensic reference only — do not invoke, extend, or import.

Original purpose (historical): two-call Skeleton->Flesh content generation
through a Plan-checker / Skeleton / Flesh / Activities / Audit pipeline.
"""
```

(Preserve the remaining body verbatim. Only the top docstring changes.)

### `scripts/build/pipeline_v5.py` — replace lines 1-5 (current docstring) with:

```python
#!/usr/bin/env python3
"""Pipeline v5 — OBSOLETE.

V5 was retired well before 2026-05-10 (superseded first by V6 and now V7).
Use ``scripts/build/v7_build.py`` + ``scripts/build/linear_pipeline.py`` for
all new work. Kept on disk for forensic reference only — do not invoke,
extend, or import.

Original purpose (historical): clean pipeline implementation; phase
implementations + state management + phase-specific helpers; imported by
``build_module_v5.py``.
"""
```

(Preserve the remaining body verbatim.)

### Optional Boy-Scout (only if zero-effort): `scripts/build/build_module_v5.py` — if it exists and has a docstring, mark it OBSOLETE in one sentence.

## Acceptance criteria

1. Both files' new docstrings include the literal token `OBSOLETE` in the first line. Verify: `grep -n 'OBSOLETE' scripts/build/v6_build.py scripts/build/pipeline_v5.py | head` — must return at least 2 lines (one per file).
2. **No code body changed in either file.** Verify: `git diff --stat scripts/build/v6_build.py scripts/build/pipeline_v5.py` — only docstring line ranges should appear; total diff < 30 lines.
3. `.venv/bin/python -c "import ast; [ast.parse(open(f).read()) for f in ['scripts/build/v6_build.py', 'scripts/build/pipeline_v5.py']]"` — must succeed (no syntax error introduced).
4. `.venv/bin/ruff check scripts/build/v6_build.py scripts/build/pipeline_v5.py` — clean.
5. Pre-existing tests still pass: `.venv/bin/pytest tests/ -k "v5 or v6" -x` (if no tests reference v5/v6 specifically that's fine; just don't break what was passing).

## #M-4 evidence (commit body)

- `head -10 scripts/build/v6_build.py` AFTER edit
- `head -10 scripts/build/pipeline_v5.py` AFTER edit
- `git diff --stat` output

## Pre-submit checklist (AGENTS.md:11-26) — applies. Total files changed = 2 (or 3 with optional Boy-Scout).

## Workflow

1. Worktree setup
2. Edit the 2 docstrings
3. Run ACs 1-4 commands; capture #M-4 evidence
4. `git add scripts/build/v6_build.py scripts/build/pipeline_v5.py` (named files only — no `git add .`)
5. `git commit -m "docs(build): mark v5/v6 OBSOLETE in module docstrings"` with body containing the evidence blocks
6. `git push -u origin codex-v5-v6-deprecate-docstrings`
7. `gh pr create` — title same as commit subject, body references this brief + the v6→V7 sweep companion PR
8. Do NOT auto-merge.
