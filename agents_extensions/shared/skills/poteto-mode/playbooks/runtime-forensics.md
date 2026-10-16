# Runtime forensics

The deliverable is a diagnosis, not a fix.

1. Capture the live signal the brief allows: a profile, a heap snapshot, or a trace. Do not attach to production, and do not print secrets.
2. Reduce it to the hot function, the retainer chain, or the loop that fires without input.
3. Confirm the mechanism with a probe the seat is allowed to run. If the probe needs a write the brief forbids, mark the mechanism unproven.
4. Map the finding to a file and a symbol.
5. Hand the cited diagnosis back. Route a fix through [bug fix](bug-fix.md) or [perf issue](perf-issue.md) only when the brief asks for a fix.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
