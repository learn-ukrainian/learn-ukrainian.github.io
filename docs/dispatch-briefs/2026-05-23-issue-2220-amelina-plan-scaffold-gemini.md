# Gemini dispatch — scaffold missing fields in amelina-women-looking-at-war plan (closes #2220)

## Mission

The plan file `curriculum/l2-uk-en/plans/lit-doc/amelina-women-looking-at-war.yaml` is missing four required top-level fields (`module`, `title`, `objectives`, `version`). `validate_plan` rejects it. Add the scaffolding so the file validates and is build-pipeline-ready. **Quality bar: every claim about the topic content must come from a tool result** (MEMORY #M-4).

## #M-4 deterministic preamble

| Claim in your output | Tool to ground it |
|---|---|
| "Plan field X already present" | `grep` the file before editing |
| "Validator passes" | `.venv/bin/python scripts/audit/validate_plan.py curriculum/l2-uk-en/plans/lit-doc/amelina-women-looking-at-war.yaml` |
| "Archive material at PATH says Y" | `cat curriculum/l2-uk-en/_archive/lit-doc/discovery/amelina-women-looking-at-war/*` and `cat curriculum/l2-uk-en/_archive/lit-doc/orchestration/amelina-women-looking-at-war/*` and paste the line you derive each field from |
| "Tests pass" | `.venv/bin/python -m pytest tests/audit/ -q` final summary line raw |

If a field's source is unclear from the archive material, leave it as a placeholder and flag in the PR body — DO NOT invent.

## Steps

1. `git worktree add` — your dispatcher handles this for `--worktree` mode; you start inside the worktree.
2. Read the current plan: `cat curriculum/l2-uk-en/plans/lit-doc/amelina-women-looking-at-war.yaml`. Note what's already present (`activity_hints`, `content_outline`, `focus`, `level: LIT.DOC`, `sequence: 13`, `slug`, `track`, `word_target: 5000`).
3. Read the archive material:
   - `curriculum/l2-uk-en/_archive/lit-doc/discovery/amelina-women-looking-at-war/`
   - `curriculum/l2-uk-en/_archive/lit-doc/orchestration/amelina-women-looking-at-war/`
   List the files first, then read the ones that look most likely to contain module-level metadata (discovery summary, plan draft, objectives doc).
4. Look at a SHIPPED lit-doc plan as a structural reference for what `module`, `title`, `objectives` look like in this track. List candidates with `ls curriculum/l2-uk-en/plans/lit-doc/` and read one that has all 4 fields present (skip stargazers — pick a fully-scaffolded sibling).
5. Add the missing fields to the YAML:
   - `module:` — derive from sequence + slug per the sibling plan's convention (e.g. `lit-doc-13` or similar; check the sibling)
   - `title:` — the module's display title (the sibling shows English/Ukrainian convention)
   - `objectives:` — list of learning objectives. Pull from the archive's objectives doc. If absent, derive 4-6 objectives from the `content_outline` and `focus` fields, framed as "Students will…" learner-actionable statements.
   - `version: 1.0.0` — fixed value per the plan-immutability hook (it expects this exact field).
6. Verify: `.venv/bin/python scripts/audit/validate_plan.py curriculum/l2-uk-en/plans/lit-doc/amelina-women-looking-at-war.yaml`. Paste the success line into your PR body.
7. Run targeted tests: `.venv/bin/python -m pytest tests/audit/test_validate_plan.py tests/audit/test_plan_invariants.py -q`. Paste the final summary line.
8. `.venv/bin/ruff check .` — should be clean (no python touched here, but the hook may run).
9. `git add curriculum/l2-uk-en/plans/lit-doc/amelina-women-looking-at-war.yaml`
10. `git commit -m "fix(plans/lit-doc): scaffold missing required fields in amelina-women-looking-at-war (closes #2220)"` — conventional commit. Body should describe which fields you added and cite the archive source for each.
11. `git push -u origin <your-branch>`
12. `gh pr create --title "fix(plans/lit-doc): scaffold missing required fields in amelina-women-looking-at-war (closes #2220)" --body "<summary + test plan>"`
13. **NO auto-merge.** Orchestrator reviews before merge.

## Out of scope

- The DETECTION followup in the issue ("scan ALL plans for missing required fields") — file as a sibling issue if you find time, but do NOT add the audit script change to this PR. Keep scope tight.
- Any other plan file. ONLY `amelina-women-looking-at-war.yaml`.

## Acceptance criteria

- The plan file has all 4 missing required fields populated from archive evidence (or marked placeholder with a TODO comment if archive is silent).
- `validate_plan.py` passes on the file.
- Targeted test suite green.
- PR opened with raw tool output (not paraphrased) in the body.
