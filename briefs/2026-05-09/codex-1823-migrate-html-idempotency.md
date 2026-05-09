# Codex CLI — `migrate_to_html.py` idempotency guard (#1823)

## TL;DR

`scripts/docs/migrate_to_html.py` (committed in `c17450a6c1`) is a one-pass MD→HTML converter. It clobbered a hand-curated `audit/codex-tools-review-2026-05-08/REPORT.html` (Gemini's PR #1816 work) on the morning's bulk run — orchestrator caught it via `git diff` and reverted, then filed this issue.

Add an idempotency check that REFUSES to overwrite hand-curated HTML, with a `--force` flag for explicit opt-in.

Full spec: **GH issue #1823** — every AC must be ticked.

---

## Mandatory orientation (#M-4)

1. **`docs/best-practices/deterministic-over-hallucination.md`** — every verifiable claim must be tool-backed.
2. **GH issue #1823** — `gh issue view 1823` — full ACs including the test matrix.
3. **`scripts/docs/migrate_to_html.py`** — read end-to-end before touching.
4. **`MEMORY.md #M-2`** — HTML/MD policy distinction between bulk batch and hand-curated.
5. **`audit/codex-tools-review-2026-05-08/REPORT.html`** (hand-curated reference) and any `audit/*/REPORT.html` produced by a prior `migrate_to_html.py` run (script-output reference) — diff these to internalize the marker convention.

## Verifiable claims this work will produce + the tool for each

| Claim | Tool | Evidence format |
|---|---|---|
| "Hand-curated HTML has `report-author` populated" | `grep -E '<meta name="report-author"' audit/codex-tools-review-2026-05-08/REPORT.html` | Quoted match |
| "Script's own output has empty/missing `report-author`" | Run script on a test MD, grep the output | Quoted match (or absence) |
| "Idempotency check refuses without `--force`" | `python scripts/docs/migrate_to_html.py <md>` against a hand-curated dest → assert exit code 1, stderr message | Quoted output |
| "`--force` overrides the refusal" | Re-run with `--force` → assert exit 0, file overwritten | Quoted output |
| "Pytest passes" | `.venv/bin/pytest tests/test_migrate_to_html.py` | Quoted output |
| "Ruff clean" | `.venv/bin/ruff check scripts/docs/migrate_to_html.py tests/test_migrate_to_html.py` | Quoted output |

The marker for "hand-curated" per the issue: **`<meta name="report-author" content="...">` populated with anything non-empty**. The script does NOT emit this. Hand-craft does.

---

## Worktree instructions (mandatory)

Dispatcher creates `.worktrees/dispatch/codex/codex-1823-migrate-html-idempotency/`. All work there. Branch: `codex/1823-migrate-html-idempotency`. Base: `origin/main`.

---

## Workflow (numbered)

1. **Worktree setup** verified.
2. **Read the issue** — `gh issue view 1823`.
3. **Read the script** — `scripts/docs/migrate_to_html.py` end-to-end.
4. **Implement the idempotency guard:**
   - Before writing `<dest>.html`, if it exists, check for `<meta name="report-author"` with non-empty content.
   - If found AND `--force` not passed → exit 1 (single-file mode) or skip+continue (batch mode), with a clear stderr line: `REFUSE: <dest> appears hand-curated (report-author=<value>); pass --force to overwrite.`
   - Add `--force` argparse flag with help text per the `cli-help-standard.md` rule.
5. **Tests** under `tests/test_migrate_to_html.py`:
   - **Test 1** — hand-curated dest exists (`report-author` set) → script refuses, exit 1, no file change.
   - **Test 2** — script's own previous output (`report-author` absent) → script overwrites freely.
   - **Test 3** — `--force` overrides refusal → exit 0, file replaced.
   - **Test 4** — fresh dest (file absent) → script writes, exit 0.
   - Use `tmp_path` fixtures, not real `audit/`/`docs/` paths.
6. **Lint** — `.venv/bin/ruff check scripts/docs/migrate_to_html.py tests/test_migrate_to_html.py`.
7. **Documentation:**
   - Script docstring: document the idempotency check + `--force`.
   - `--help`: per `cli-help-standard.md`, ensure description, every flag has help, epilog with examples + Outputs/Exit codes/Related.
   - `MEMORY.md #M-2` append: *"`migrate_to_html.py` refuses to overwrite hand-curated HTML (`<meta report-author>`-marked); use `--force` only with explicit user signoff."*
8. **Commit** — conventional message:
   ```
   fix(scripts): make migrate_to_html.py idempotent for hand-curated HTML (#1823)

   - REFUSE overwrite if dest has <meta report-author> populated.
   - --force flag for explicit opt-in.
   - Tests covering 4 cases (hand-curated, script-own, force, fresh).
   - Docs + --help conform to cli-help-standard.

   Closes #1823.

   Co-Authored-By: Codex (gpt-5.5) <noreply@anthropic.com>
   ```
9. **Push** — `git push -u origin codex/1823-migrate-html-idempotency`.
10. **PR** — `gh pr create` referencing #1823, every AC ticked with quoted evidence per #M-4.
11. **NO auto-merge.** Stop. Orchestrator handles cross-agent review and merge.

---

## What "done" looks like

- All ACs from #1823 ticked in PR body with evidence.
- 4 tests pass.
- Pre-commit clean.
- PR opened, **NOT merged**.

## Escalation

If the script architecture forces a different marker convention (e.g. `report-author` already populated by your script for some reason), STOP, post on #1823 with the finding + proposal, exit cleanly.
