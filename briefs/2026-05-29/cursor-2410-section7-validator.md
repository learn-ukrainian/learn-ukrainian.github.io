# Cursor brief — Deterministic §7 cross-track path validator (#2410)

## Why
Bio research dossiers (`docs/research/bio/*.md`) repeatedly cite FABRICATED "Existing" plan paths
in Section 7 ("Cross-track links") — invented filenames that don't exist in `curriculum/l2-uk-en/plans/`.
Confirmed in PRs #2400/#2409 + ~12 already-merged R1a dossiers. A prompt-only fix (commit `5ef63e8cdc`)
did NOT bind the generating models. The fix is a DETERMINISTIC gate.

## Build (2 deliverables)

### 1. Validator script `scripts/audit/lint_bio_dossier_xref.py`
- Scan every `docs/research/bio/*.md`. Parse Section 7 ("## 7. Cross-track links").
- Extract every cited path matching `(?:docs/)?plans/[\w-]+/[\w-]+\.yaml`.
- For each path under an **"Existing"** bullet (heading text contains "Existing"), normalize by stripping
  a leading `docs/` and resolve against `curriculum/l2-uk-en/<path>`. If `not Path.exists()` → it's a
  FABRICATION → report `{file, line, path, bullet_context}`.
- Paths under "Potential"/"Candidate"/"Phase 2+" bullets are EXEMPT (forward-looking, may not exist).
- Exit non-zero if any fabrication found; print a clean table. Add `--fix` is NOT required.
- CLI: `.venv/bin/python scripts/audit/lint_bio_dossier_xref.py [--paths docs/research/bio/*.md]`.
  Follow the existing CLI/exit-code conventions in `scripts/audit/` (look at a sibling linter, e.g.
  `scripts/audit/lint_agent_trailer.py`, for the house pattern + argparse style).

### 2. Wire it into pre-commit
- Add a `pre-commit` hook in `.pre-commit-config.yaml` (a `local` repo hook, `language: system`,
  `files: ^docs/research/bio/.*\.md$`) that runs the validator on changed dossiers. Model it on the
  existing local hooks already in that file.

### 3. Tests `tests/test_lint_bio_dossier_xref.py`
- A fixture dossier with a fabricated "Existing" path → validator FAILS, names the path.
- A fixture with only real paths + "Potential" candidates → validator PASSES.
- A real "Existing" path that exists → PASSES.

### 4. Run it across the repo + report (do NOT fix the dossiers in this PR)
- Run the validator over all current `docs/research/bio/*.md` and PASTE the raw fabrication report
  into the PR body. (~12 fabrications expected in already-merged R1a dossiers — a follow-up sweep PR
  will fix them; this PR just builds + lands the gate and documents the backlog.)

## Verification (#M-4 — quote raw)
- `.venv/bin/python -m pytest tests/test_lint_bio_dossier_xref.py -q` → final `N passed` line.
- `.venv/bin/ruff check scripts/audit/lint_bio_dossier_xref.py tests/test_lint_bio_dossier_xref.py` → `All checks passed!`.
- `pre-commit run lint-bio-dossier-xref --all-files` (or the hook id you chose) → show it runs.

## Steps (dispatch enforces worktree)
1. Confirm worktree root.
2. Build script + hook + tests.
3. Run pytest + ruff (paste raw final lines).
4. Run the validator over `docs/research/bio/*.md`, capture the fabrication report for the PR body.
5. `git commit` conventional (`feat(audit): deterministic §7 cross-track path validator for bio dossiers (#2410)`); Co-Authored-By line.
6. `git push -u origin <branch>` ; `gh pr create --base main`. **No auto-merge.**
Report: PR URL (raw), pytest line, ruff line, and the fabrication-report table.
