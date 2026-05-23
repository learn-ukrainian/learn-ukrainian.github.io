# Claude — CodeQL + security + awaiting PRs (2026-05-23)

## Mission
Clear the open CodeQL alerts, investigate the dependabot security/PR backlog
Agy left behind, and close out the awaiting PRs. **Investigate root causes;
do NOT mass-merge.** Quality bar is "every action defensible by a tool-backed
claim" (MEMORY #M-4).

## Scope at session start (verified by orchestrator)

### CodeQL alerts (3) — all `note` severity
| # | Rule | Path |
|---|---|---|
| 209 | `zizmor/dependabot-cooldown` | `.github/dependabot.yml:16` |
| 210 | `zizmor/dependabot-cooldown` | `.github/dependabot.yml:34` |
| 211 | `zizmor/dependabot-cooldown` | `.github/dependabot.yml:49` |

zizmor flags missing `cooldown:` blocks on Dependabot package-ecosystem
configs (recommended to avoid version-bump churn). Fix is mechanical: add
a `cooldown:` block to each `updates:` entry per the zizmor docs. **Do
NOT silence the rule** unless after-the-fact research surfaces a reason
the cooldown convention should not apply here.

### Awaiting PRs
| # | Subject | State |
|---|---|---|
| 2168 | fix(curriculum): backfill seminar `references[].title` (closes #2164) | `Curriculum Plans` CI **FAILED** |
| 2191 | astro 6.3.1 → 6.3.3 (starlight) | rebase requested by Agy (was behind main) |
| 2190 | accelerate 1.12 → 1.13 | rebase requested by Agy |
| 2189 | click 8.3.1 → **8.4.0** (dependabot bumped during the day) | rebase requested by Agy |
| 2188 | flask 3.1.2 → 3.1.3 | rebase requested by Agy |
| 1873 | @astrojs/starlight 0.38.4 → 0.39.2 | **escalated** — breaking sidebar-schema change. See Agy comment `https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/1873#issuecomment-4519976655` |

### Dependabot security alerts
API call returned **HTTP 403** ("Dependabot alerts are disabled for this
repository"). Either the feature is off org-wide or the orchestrator's
token lacks `admin:repo_hook`. **Skip this layer** unless `gh api` from
your dispatched session has different auth; do not enable a setting.

## Tasks, in execution order

### Task 1 — CodeQL `dependabot-cooldown` (3 alerts)

1. `git worktree` is already provided to you (`.worktrees/dispatch/claude/...`).
2. `cat .github/dependabot.yml` — read the three blocks at lines 16, 34, 49.
3. Read zizmor's recommendation for `dependabot-cooldown`. The canonical fix
   is adding:

   ```yaml
   cooldown:
     default-days: 7
     # Or: per-update-type matrix if the team has stricter rules for major
     #   vs minor vs patch — start with a flat 7-day default and refine later.
   ```

   under each affected `updates:` entry. Use the same default-days value across
   all three blocks unless the existing block has a different cadence (e.g.
   weekly schedule) where a shorter cooldown is justified — in which case
   explain in the commit.

4. Verify the YAML still parses: `yamllint .github/dependabot.yml || true`
   (zizmor + yamllint may reject for unrelated reasons; the only blocker is
   GitHub's validator which fires when the PR opens).

5. Commit: `chore(dependabot): add cooldown blocks to silence zizmor/dependabot-cooldown (#209-#211)`.

6. Open PR. Wait for CI. If `zizmor` check turns green (alerts auto-close
   from `dismissed_at` field on the alert API), the fix landed. If still
   red, post the failure log + your interpretation in the PR description and
   STOP — do NOT push another speculative fix.

### Task 2 — PR #2168 (seminar refs `title:` backfill)

1. `gh pr checkout 2168` into a fresh worktree.
2. `gh run view <failed-run-id> --log-failed` — get the `Curriculum Plans`
   failure body. Quote the raw `assert` line in your commit message.
3. Root-cause it. The PR backfills `references[].title` across ~20 seminar
   plans (closes #2164 per the title). The CI is likely a validate_plan-style
   schema check; one of the backfilled titles probably doesn't match a
   required pattern (e.g. min-length, no-trailing-period, expected casing).
4. Fix at the layer of the actual bug:
   - If a backfilled title is genuinely wrong → fix that title.
   - If validate_plan is too strict → tighten the brief; consider whether
     it's a validator bug or a content bug. Prefer the latter if it's
     1-2 titles vs. dozens.
5. **Do NOT touch the validator** to make red turn green if the data is the
   problem.
6. Commit, push, watch CI.
7. Once green: `gh pr merge 2168 --squash --delete-branch` IF blocking CI
   green. Bring back to user if any cross-track invariant change is needed.

### Task 3 — PR #1873 (starlight 0.39.2 breaking change)

Agy flagged: starlight 0.39.2 enforces a stricter sidebar schema. Our
`autogenerate` entries (B2-PRO, C1-PRO, OES, RUTH, etc.) fail the new
union validator with:

```
'sidebar.11': Did not match union.
> Expected type `{ link: string } | { items: array } | { slug: string } | string`
> Received `{ "label": "...", "autogenerate": { "directory": "..." }, "collapsed": true }`
```

1. Read `starlight/CHANGELOG.md` for 0.38.4 → 0.39.x to confirm the breaking
   change. (Starlight typically logs schema-breaking changes prominently.)
2. The error message implies the union expects four shapes but ours uses a
   FIFTH (`autogenerate`-based). Check whether `autogenerate` was renamed,
   moved into a different field, or now needs a top-level `slug` first.
3. Fetch the migration guide if linked. **Do not guess.**
4. **TWO outcomes possible:**
   - **(a) Local config needs to migrate.** Update `astro.config.mjs` in
     `/starlight` accordingly, run `npm run build` in `/starlight`, confirm
     green. Push as a follow-up commit on `#1873`.
   - **(b) Starlight 0.39 is a no-go for our setup.** Either we wait for a
     follow-up release, or pin to 0.38.x. Comment on #1873 with the
     finding + closing recommendation; do NOT close it yourself.

5. Cap your time at 45 minutes on this one. If you can't find the migration
   path, post your investigation log and STOP.

### Task 4 — Dependabot rebase-requested PRs (#2188, #2189, #2190, #2191)

By the time you read this, dependabot may have force-pushed rebased commits.
For each PR:

1. `gh pr view N --json statusCheckRollup` — see if CI is now green.
2. If green + `mergeable: MERGEABLE` → `gh pr merge N --squash --delete-branch`.
3. If still red → fetch the failed log. If it's the same "featured slugs"
   error Agy diagnosed, the rebase didn't take — re-comment `@dependabot rebase`
   ONCE and move on. If it's a NEW failure, root-cause it.
4. Do NOT investigate features/etymology data changes from `main` as part
   of this task — those are out of scope. Just ferry the PRs through.

### Task 5 — Dependabot security alerts

Skipped per the 403 — the orchestrator could not enumerate them. If your
session has higher scope (`gh auth status` shows `admin:repo_hook`),
`gh api repos/learn-ukrainian/learn-ukrainian.github.io/dependabot/alerts?state=open`
and triage by severity (critical / high / moderate / low). For each:
- `critical` / `high`: file an issue + comment in the appropriate dependency
  PR (if one exists) referencing the advisory.
- `moderate` / `low`: catalog into a follow-up doc but don't auto-act.

Do NOT enable a feature on the repo (org-policy decision).

## Hard rules

- **#M-0.5 NEVER admin-bypass blocking CI.** Patient, root-cause merges only.
  `--admin` flag forbidden.
- **#M-7 PYTEST BEFORE PUSH.** Any code change touching `.github/`, `scripts/`,
  `tests/`, `curriculum/`, or `.dagger/` requires
  `.venv/bin/python -m pytest tests/test_<x>.py` of the affected fixture file.
  YAML-only edits in `.github/dependabot.yml` do NOT require pytest (no
  fixture mirror).
- **#M-4 DETERMINISTIC OVER HALLUCINATION.** Every "I did X" claim in your
  final report MUST be backed by a quoted command output (SHA, raw CI line,
  raw lint output). No "tests pass" without a `pytest` summary line. No
  "merged" without the `gh pr merge` SHA.
- **No new ADRs.** This is mechanical cleanup.

## Per-task PR checklist (when you open one)

1. `git worktree` already provided.
2. Branch name `claude/<task-slug>-2026-05-23`.
3. Commits conventional (`chore:`, `fix:`, `feat:`).
4. Acceptance-criteria block at the END of each commit message with the
   verifiable outputs the test plan referenced.
5. `git push -u origin <branch>`.
6. `gh pr create --title ... --body ...` with HEREDOC body that includes:
   - Summary (3-5 bullets)
   - Verifiable claims table (claim → command → raw output line)
   - Test plan checklist
7. **Do NOT auto-merge** anything you OPEN. Only auto-merge the in-flight
   dependabot PRs from Task 4 if their CI greens cleanly.
8. Final report at end-of-session: per-task table + status + SHA.

## Final report format (REQUIRED)

```
Task | Subject                                    | Action     | Outcome
-----+--------------------------------------------+------------+--------------------
1    | CodeQL dependabot-cooldown #209-#211       | PR opened  | #NNNN @ <sha>
2    | PR #2168 Curriculum Plans CI red           | merged     | squashed @ <sha>
3    | PR #1873 starlight 0.39.2 schema breakage  | escalated  | comment URL
4a   | PR #2188 flask rebase                      | merged     | squashed @ <sha>
4b   | PR #2189 click rebase                      | merged     | ...
4c   | PR #2190 accelerate rebase                 | rebase req | ...
4d   | PR #2191 astro rebase                      | merged     | ...
5    | Dependabot alerts                          | skipped    | 403 — feature off
```

Plus a 4-7 line prose summary at the bottom highlighting anything that
needs orchestrator follow-up.

## What success looks like

- CodeQL alert count drops from 3 to 0 once your PR merges.
- PR #2168 is either merged or has a clear "blocked because X" comment with
  the next concrete action.
- PR #1873 has Either a working migration PR Or a definitive "pin 0.38.x"
  recommendation comment with the migration-doc link as evidence.
- The 4 dependabot rebase PRs are either merged or have a documented
  blocker.

## Out of scope

- Touching the V7 build pipeline
- Editing curriculum content (you may touch `references[].title` strings in
  seminar plans ONLY as part of Task 2)
- Word Atlas v1 work — orchestrator owns that track
- Refiring any builds
- Promoting any modules
