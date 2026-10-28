---
description: Who may run the delivery skills (full-send, full-stop, review-loop, takeover, modernize, pr-comments)
alwaysApply: true
---

# Delivery skills

Cursor loads the shared skills from `.agents/skills/`. Use them by
name. Source: `agents_extensions/cursor/rules/delivery-skills.md`.

- `full-send` — deliver a change to MERGED and closeout. The worker that receives a brief, the
  accountable driver of the PR's stream, the integration owner or the CTO.
- `full-stop` — deliver to ready-to-merge and never merge. Use it when the brief says so or the
  merge belongs to another driver.
- `review-loop` — review rounds to a recorded verdict; the budget is in its
  `references/policy.md`. The worker that owns the brief or a driver runs it; the resolver
  picks the reviewer.
- `takeover`, `modernize` — entry skills that end in a hand-off record for `full-send` or
  `full-stop`. A worker under a brief runs the chain itself; closing the original or a
  superseded PR is a driver act.
- `pr-comments` — every agent comment on GitHub.

A worker seat runs its chain to the end (rules core P1): `review-loop`, enqueue after the
recorded exact-head verdict and green CI, MERGED, closeout; `full-stop` only when its brief
says so. Nobody arms auto-merge. The skills never override the repository rules or the
operator-only list.
