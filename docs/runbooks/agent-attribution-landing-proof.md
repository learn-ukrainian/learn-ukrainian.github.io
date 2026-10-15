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

pending landing
