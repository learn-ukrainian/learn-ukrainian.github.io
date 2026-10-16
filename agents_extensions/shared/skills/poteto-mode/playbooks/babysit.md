# Babysit

Drive a pull request toward merge-ready. This playbook does not merge, enqueue, or retarget a stack.

1. Say whether you are driving the lowest open pull request to green, or only triaging.
2. Work the lowest unmerged pull request. Read upper threads. Do not fix them ahead of the frontier.
3. One owner per stack. Do not retarget, force-push, or rebase the stack from here. A conflict is reported, not rewritten, unless the brief assigns that branch to you.
4. Order: conflicts, then review findings, then CI. Batch fixes into one push on the owning branch.
5. Classify a CI failure from the job log before any rerun. One recovery attempt for an unchanged approved head, and only when the failure is shown to be infrastructure or a matched flake, per `workflow.md`. A second failure stops.
6. Treat automated review comments as claims. Verify each against the diff (`../../interrogate/SKILL.md`). Fix a real defect with a failing-then-passing check. Dismiss noise with a reason.
7. Stop at owner approval and at merge. Landing is [shipping](shipping.md), and only the driver does it.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
