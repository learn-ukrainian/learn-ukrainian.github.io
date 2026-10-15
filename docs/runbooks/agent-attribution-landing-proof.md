# Agent attribution landing proof

## Contract

An agent attribution is a line matching `^X-Agent: <agent>/<task-id>$` in the
landed commit message. It is a plain line, not a parseable git trailer, because
GitHub appends a `Co-authored-by` paragraph after the body of a squash commit.
Tools must therefore match the line, never rely on trailer parsing.

## Setting readback

| Repository setting | Value |
| --- | --- |
| `squash_merge_commit_title` | `PR_TITLE` |
| `squash_merge_commit_message` | `COMMIT_MESSAGES` |

Read on 2026-10-15T18:04:02Z by the operator via the repository settings page
(issue 10736, slice A1 of program 9737).

## Result

Verify after the PR is merged to `main`:

1. Find the merge commit on `main` for this PR (the squash commit).
2. Run `git log -1 --format=%B <merge sha on main>`.
3. The output must contain both of these lines, each on its own line:
   - `X-Agent: claude/impl-10736-a1-proof-c1`
   - `X-Agent: claude/impl-10736-a1-proof-c2`

Pass means both lines are present. Fail means either is missing, for example
if the squash used only the PR title and body. The driver records the actual
outcome on the issue after merge; this page holds only the recipe.
