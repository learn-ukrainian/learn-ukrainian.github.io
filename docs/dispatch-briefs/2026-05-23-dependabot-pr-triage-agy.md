# Agy — Dependabot PR triage (2026-05-23)

## Task
Triage and merge (or close with reason) all 8 currently-open Dependabot PRs.

## Scope
| # | Subject |
|---|---|
| 2192 | ci: bump actions/setup-node 6.3.0 → 6.4.0 (github-actions group) |
| 2191 | deps: bump astro 6.3.1 → 6.3.3 in /starlight |
| 2190 | deps: bump accelerate 1.12.0 → 1.13.0 |
| 2189 | deps: bump click 8.3.1 → 8.3.3 |
| 2188 | deps: bump flask 3.1.2 → 3.1.3 |
| 2142 | deps: bump onnxruntime 1.23.2 → 1.24.3 |
| 2139 | deps: bump virtualenv 21.2.0 → 21.3.3 |
| 1873 | deps: bump @astrojs/starlight 0.38.4 → 0.39.2 in /starlight |

## Steps per PR (in order)
1. `gh pr view {N} --json statusCheckRollup,mergeStateStatus,mergeable`
2. **Decision tree:**
   - All blocking CI green + `mergeable: MERGEABLE` → `gh pr merge {N} --squash --delete-branch`
   - Blocking CI red → fetch the failed log: `gh run view <id> --log-failed | tail -50` and report root cause; do NOT auto-fix
   - Major version bump that touches build/runtime → comment with risk assessment, do NOT auto-merge; escalate
   - Patch/minor bump and tests green → merge
3. After merge: confirm `gh pr view {N} --json state` returns `MERGED`
4. **Rebase if base is stale:** if `mergeStateStatus: BEHIND`, comment `@dependabot rebase` and move on to next PR; come back later

## Hard rules
- **NEVER admin-bypass blocking CI.** `--admin` is forbidden for these per MEMORY #M-0.5.
- **Blocking checks:** Test (pytest), Lint (ruff), Frontend (build + vitest), Secret Scanning (gitleaks), Lesson Schema Drift, Quality Gates (radon), Lint Prompts.
- **Advisory checks** (don't block on these): `review / review` (Gemini-Dispatch — known broken auth).
- Major version bumps (1.x → 2.x or 0.x → 1.x) on runtime deps require human escalation — leave a comment, do not merge.
- Patch bumps on dev/test-only deps can merge without changelog review.

## Output (REQUIRED — final assistant message)
Status table:

```
PR    | Subject                       | Action       | Outcome
------+-------------------------------+--------------+--------------------
2192  | actions/setup-node 6.3 → 6.4  | merged       | squashed @ <sha>
2191  | astro 6.3.1 → 6.3.3           | rebase req   | @dependabot rebase posted
...
```

Plus a short prose footer listing any PRs that need human review and why.

## Anti-fabrication
Every "merged" row MUST include the SHA returned by `gh pr merge`. Every "rebase req" row MUST include the comment URL. Do not write "all done" without the table.

## Sequencing
Process in this order (cheapest-blast-radius first):
1. **Dev-only / lint-only**: virtualenv (#2139), click (#2189) — patch bumps, low risk
2. **CI infra**: actions/setup-node (#2192) — minor CI bump
3. **Backend runtime**: flask (#2188), accelerate (#2190), onnxruntime (#2142) — patch/minor, verify tests green
4. **Frontend**: astro (#2191), @astrojs/starlight (#1873) — verify Frontend (build + vitest) CI green before merge

## Not in scope
- Opening NEW dependabot PRs
- Touching non-dependabot PRs
- Modifying any code outside what dependabot itself proposed
