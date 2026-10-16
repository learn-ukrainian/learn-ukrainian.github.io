# Autopilot full

A queue of independent pull requests, each with one owner. Nothing in this playbook authorizes a merge by a worker, a swarm vote, or an N-implementation arena.

1. The queue is the grant. Items outside it stop at report.
2. The driver assigns one owner per pull request, on disjoint branches off the base. Owners do not stack on each other.
3. Verification at the code-ready head is `../../local-code-review/SKILL.md` plus the brief's tests. A rebase needs a fresh look at the moved head. A panel is not the review of record.
4. The driver lands only a head that still has exact-head approval and green CI (`shipping`).
5. On a stop, owners stop writing and report where they stand.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
