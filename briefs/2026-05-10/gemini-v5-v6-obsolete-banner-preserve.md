# Gemini brief — v5/v6 OBSOLETE banner (PRESERVE original docstring)

**Issue:** N/A. Replaces closed PR #1851 (which destroyed forensic content by replacing docstrings instead of prepending). Gemini's adversarial review on #1851 caught the bug.
**Task ID:** `gemini-v5-v6-obsolete-banner`
**Mode:** `--mode danger --worktree`
**Base:** `origin/main`

## Worktree

```
git worktree add -b gemini-v5-v6-obsolete-banner .worktrees/gemini-v5-v6-obsolete-banner origin/main
cd .worktrees/gemini-v5-v6-obsolete-banner
```

## Why this is a re-do

Previous PR #1851 (Codex) followed a brief that told it to **replace** the existing docstrings. That destroyed the forensic value the files exist to preserve:

- `scripts/build/v6_build.py` lost: the 9-step pipeline (CHECK → RESEARCH → SKELETON → WRITE → EXERCISES → VERIFY → ANNOTATE → VERIFY → REVIEW → PUBLISH), the Skeleton→Flesh architectural rationale (#998 — "prevents frontloading early sections and rushing later ones"), 8 usage examples covering `--no-skeleton`, `--step`, `--writer`, `--resume`, `--range` flags, and issue refs `#993` / `#998`.
- `scripts/build/pipeline_v5.py` lost: the pipeline-shape line, the `#820` sandbox-phase removal note, the `state.json` mode marker.
- `scripts/build/build_module_v5.py` got a more careful treatment (kept usage examples), but inconsistent with the other two.

User confirmed: keep the forensic content, just add the OBSOLETE marker. **PRESERVE — do not REPLACE.**

The whole point of keeping these files on disk is "forensic reference only." Throwing away the forensic content while keeping the file is the worst of both worlds.

## What to change (precise pattern)

For each of `scripts/build/v6_build.py`, `scripts/build/pipeline_v5.py`, `scripts/build/build_module_v5.py`:

1. Read the file's current top-of-file docstring **as it exists on `origin/main` right now** (NOT the version in #1851's diff — that PR is being closed).
2. Insert a new OBSOLETE banner at the very top of the docstring (between the opening `"""` and the existing first line).
3. Preserve every other line of the original docstring verbatim — every word, every issue ref, every example, every line break.

### Banner template (use exactly this; substitute the per-file note where indicated)

```
{FILE_TITLE} — OBSOLETE (retired 2026-05-10).

Use ``scripts/build/v7_build.py`` for all new builds. This file is kept on
disk for forensic reference only — do not invoke, extend, or import.
{FILE_NOTE}

--- Historical docstring preserved below ---

{EXISTING_DOCSTRING_VERBATIM}
```

### Per-file substitutions

**`scripts/build/v6_build.py`** — `{FILE_TITLE}` is `V6 Pipeline Build`. `{FILE_NOTE}`: blank (V6 was the most recent retired pipeline).

**`scripts/build/pipeline_v5.py`** — `{FILE_TITLE}` is `Pipeline v5`. `{FILE_NOTE}`: `V5 was retired well before V6; superseded first by V6 and now V7.`

**`scripts/build/build_module_v5.py`** — `{FILE_TITLE}` is `E2E Module Builder v5`. `{FILE_NOTE}`: `V5 was retired well before V6.`

### Concrete example — `scripts/build/v6_build.py`

The existing top of the file (verify with `head -38 scripts/build/v6_build.py` on `origin/main`):

```python
#!/usr/bin/env python3
"""V6 Pipeline Build — two-call Skeleton->Flesh content generation.

Orchestrates the V6 pipeline:
1. CHECK: Plan checker validation
2. RESEARCH: Build knowledge packet from RAG
... [many lines of original content] ...

Issue: #993, #998
"""
```

Becomes:

```python
#!/usr/bin/env python3
"""V6 Pipeline Build — OBSOLETE (retired 2026-05-10).

Use ``scripts/build/v7_build.py`` for all new builds. This file is kept on
disk for forensic reference only — do not invoke, extend, or import.

--- Historical docstring preserved below ---

V6 Pipeline Build — two-call Skeleton->Flesh content generation.

Orchestrates the V6 pipeline:
1. CHECK: Plan checker validation
2. RESEARCH: Build knowledge packet from RAG
... [many lines of original content] ...

Issue: #993, #998
"""
```

Note the original first line ("V6 Pipeline Build — two-call Skeleton->Flesh content generation.") is now the **second** title line of the combined docstring — it's preserved verbatim as part of the historical block, NOT renamed.

Apply the same pattern to all three files. The result is one combined docstring per file that contains: OBSOLETE banner → preservation note → original docstring verbatim.

## Acceptance criteria

1. **Original content fully preserved.** For each of the 3 files, the original docstring text from `origin/main` HEAD must appear verbatim (every line, every word, every reference) below the new banner. Verify per file:

   ```bash
   git show origin/main:scripts/build/v6_build.py | sed -n '/^"""/,/^"""/p' > /tmp/v6_orig.txt
   sed -n '/^"""/,/^"""/p' scripts/build/v6_build.py > /tmp/v6_new.txt
   # Every line in /tmp/v6_orig.txt (excluding the surrounding """ lines and the original first line "V6 Pipeline Build — two-call ...") must also appear in /tmp/v6_new.txt
   diff <(grep -vF '"""' /tmp/v6_orig.txt) <(grep -vF '"""' /tmp/v6_new.txt) | grep '^<' && echo "PRESERVATION FAILED: original lines missing" || echo "PRESERVATION OK"
   ```

   For all 3 files: must report `PRESERVATION OK`.

2. **New banner present.** `grep -n 'OBSOLETE (retired 2026-05-10)' scripts/build/v6_build.py scripts/build/pipeline_v5.py scripts/build/build_module_v5.py` returns 3 matches.

3. **No code body changes.** `git diff --stat` shows only docstring lines added (no removals from outside the docstring; no Python statements changed). Diff per file should be roughly `+10/-0` to `+12/-0` (banner + preservation note + blank lines).

4. **Files still parse + import where applicable.**

   ```bash
   .venv/bin/python -c "import ast; [ast.parse(open(f).read()) for f in ['scripts/build/v6_build.py', 'scripts/build/pipeline_v5.py', 'scripts/build/build_module_v5.py']]"
   ```

5. `.venv/bin/ruff check scripts/build/v6_build.py scripts/build/pipeline_v5.py scripts/build/build_module_v5.py` clean.

6. `.venv/bin/pytest tests/ -k "v5 or v6 or build_module" -x` — pre-existing tests still pass (don't break anything that was passing on main).

## #M-4 evidence (commit body)

For each of the 3 files, paste:

- `head -25 scripts/build/{file}` AFTER edit (shows the new banner + start of preserved original).
- The `PRESERVATION OK` confirmation line from AC 1 for that file.

Plus:

- `git diff --stat` output (should show only the 3 files, +30/-0 to +36/-0 total).

## Pre-submit checklist (AGENTS.md:11-26) — applies. 3 files changed, well under 20.

## Workflow

1. Worktree setup
2. For each file: read current top docstring on `origin/main`, prepend OBSOLETE banner block, preserve original verbatim.
3. Run AC commands; capture #M-4 evidence outputs.
4. `git add scripts/build/v6_build.py scripts/build/pipeline_v5.py scripts/build/build_module_v5.py` (named files only).
5. `git commit -m "docs(build): prepend OBSOLETE banner to v5/v6, preserve historical docstrings"` with body containing the preservation-OK confirmations + head outputs + git diff --stat.
6. `git push -u origin gemini-v5-v6-obsolete-banner`.
7. `gh pr create` — title same as commit subject, body references this brief and the closed predecessor #1851.
8. Do NOT auto-merge. Tag the PR body: *"Replaces #1851 (closed). Preserves forensic content per Gemini adversarial review."*
