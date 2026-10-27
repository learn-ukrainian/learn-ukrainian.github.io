# Delivery skills (Cursor)

Deployed digest: `.cursor/rules/delivery-skills.mdc` (`alwaysApply`).

Cursor loads the shared skills from `.agents/skills/`, which
`npm run agents:deploy` writes. Use them by name; this rule only states who may run which.

| Skill | Use it to | Who may run it |
| --- | --- | --- |
| `full-send` | Deliver a change to MERGED and closeout | Accountable driver of the PR's stream, integration owner, CTO |
| `full-stop` | Deliver a change to ready-to-merge, never merging | Anyone, including workers |
| `review-loop` | Run review rounds and the budget to a recorded verdict | The driver; a worker asks its driver |
| `takeover` | Continue someone else's PR, branch, issue or task | Driver, or a worker under a brief; a worker never closes, merges or enqueues |
| `modernize` | Bring old work up to date, or scope one area | Driver, or a worker under a brief; a worker never closes, merges or enqueues |
| `pr-comments` | Post an agent comment safely | Everyone |

A Cursor worker seat never merges, enqueues or arms auto-merge, and never dispatches
reviewers: it runs `full-stop` and hands the PR to its driver. The skills never override the
repository rules or the operator-only list.
