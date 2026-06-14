# Dispatch: resolve 8 lit slug-mismatch errors blocking validate_plan_ordering.py promotion (#2526)

`validate_plan_ordering.py` reports 8 `lit`-track errors where YAML `slug` ≠ filename-derived expected
slug. The issue notes these look like INTENTIONAL slug≠filename (unlike bio's content-duplicate case).
Read it first: `gh issue view 2526`. Goal: **0 lit errors from `validate_plan_ordering.py` WITHOUT breaking
any live module URL.**

## The 8 (slug → expected-from-filename)
bahrianyi-tyhrolovy/bahrianyi-tiger-trappers · chorna-rada-roman/black-council-plot ·
franko-titan-pratsi/franko-biography · kotsiubynsky-intermezzo/kotsiubynsky-apple-blossom ·
lesia-ukrainka-kassandra/lesia-in-the-catacombs · tanja-maljartschuk/tanja-maljartschuk-biography ·
shevchenko-ran-balady/the-ballads · zapovit/the-testament

## Decide intent PER slug (do not blindly rename)
For each, determine which is canonical/live:
- Is a module already PUBLISHED under the YAML `slug`? Check `site/src/content/docs/lit/` (or wherever lit
  MDX lives) + `curriculum/l2-uk-en/lit/` + `curriculum.yaml` + any cross-links (`grep -rn <slug>`).
- **If the YAML slug is the live/canonical one** (published, linked): the correct fix is to make
  `validate_plan_ordering.py` treat an explicit `slug` field as AUTHORITATIVE (filename need not equal slug)
  — add a minimal, well-tested allowance, NOT a per-file hack. Document why slug≠filename is legitimate.
- **If the filename is canonical** (nothing published under the slug): correct the YAML `slug` to match.
- Likely a MIX — handle each on its evidence; produce a per-slug decision table in the PR body.

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin` (you are in a `--worktree` from origin/main).
2. Investigate the 8; apply the minimal correct fix per the rule above.
3. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python scripts/audit/validate_plan_ordering.py` (find exact path with `git grep -l validate_plan_ordering`) → **0 lit errors**.
4. If you changed the validator: `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest -k "plan_ordering or validate_plan" -q` → paste summary.
5. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check .` → paste final line.
6. Commit `fix(lit): resolve 8 slug-mismatch errors for validate_plan_ordering promotion (#2526)`.
7. `git push -u origin <branch>`; `gh pr create` referencing #2526. NO auto-merge.

## Evidence (#M-4 — command + cwd + raw output per claim)
- validator before/after (raw output showing 8 lit errors → 0); per-slug decision table; tests summary if
  validator changed; ruff final line; `git log -1 --oneline`; `gh pr view --json url`.
