---
name: how
description: Explain how a subsystem works from the code, without spawning explorers.
  Use for /how.
---

# How

Explain how the code works from the files themselves. Do not spawn explorer or explainer subagents.

1. Name the question and the entry point.
2. For a single function, read it and its direct callers. For a subsystem, follow one realistic request from the entry to the state it writes.
3. Note lifecycle edges that matter: startup, retry, cache, teardown.
4. Present, in this order: what it is, the path of one request, the state it owns, and what you could not find. An empty search is unknown, not proof of absence.

Cite file paths. Do not invent a call that you did not read. Investigation does not change files (`poteto-mode` playbook `investigation`).

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
