---
name: create-verification-skill
description: Describe a project-local way to prove user-visible behavior, using the
  checks the repo already has. Use for /create-verification-skill.
---

# Create a verification skill

Interview the repository before inventing a harness.

1. Name the surface a user touches, the documented command that starts it, how an agent can drive it, what evidence can be captured, and whether two instances can run at once.
2. Prefer an existing check. In this repository that includes the task's named tests and `agents_extensions` skills that already prove a surface. Do not generate a second launcher, a process killer, or a script that runs in every session.
3. If a gap remains, draft a skill whose steps are: start from a clean state, a read-only doctor, drive the real user path, capture evidence, and clean up only what that run created. Seed a feature map with one row per user-visible behavior: entry, drive step, success evidence, cleanup. Take rows from existing tests and docs, not from a sample app.
4. Prove the draft on one feature before handing it to the driver. A new skill is a proposal. It is not deployed and not approved by this skill.

Do not put secrets, ports of shared services, or host paths in the draft.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
