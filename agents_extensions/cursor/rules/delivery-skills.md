# Delivery skills (Cursor)

Deployed digest: `.cursor/rules/delivery-skills.mdc` (`alwaysApply`).

Cursor loads the shared skills from `.agents/skills/`, which
`npm run agents:deploy` writes. Use them by name; this rule only states who may run which.

| Skill | Use it to | Who may run it |
| --- | --- | --- |
| `full-send` | Deliver a change to MERGED and closeout | The worker that receives a brief, the accountable driver of the PR's stream, integration owner, CTO |
| `full-stop` | Deliver a change to ready-to-merge, never merging | Anyone, when the brief says so or the merge belongs to another driver |
| `review-loop` | Run review rounds to a recorded verdict (budget: its `references/policy.md`) | The worker that owns the brief, or a driver; the resolver picks the reviewer |
| `takeover` | Continue someone else's PR, branch, issue or task | Driver, or a worker under a brief, which runs the chain itself; closing the original PR is a driver act |
| `modernize` | Bring old work up to date, or scope one area | Driver, or a worker under a brief, which runs the chain itself; closing a superseded PR is a driver act |
| `pr-comments` | Post an agent comment safely | Everyone |

A Cursor worker seat runs its chain to the end (rules core P1): `review-loop`, enqueue after
the recorded exact-head verdict and green CI, MERGED, closeout; `full-stop` only when its brief
says so. Nobody arms auto-merge. The skills never override the repository rules or the
operator-only list.
