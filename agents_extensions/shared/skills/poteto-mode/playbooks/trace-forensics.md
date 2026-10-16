# Trace forensics

Diagnose a captured profile or heap snapshot. The deliverable is a diagnosis, not a fix.

1. Identify the format. Reduce large artifacts outside the reply (`../../principle-guard-the-context-window/SKILL.md`). A queryable table beats a pasted dump.
2. Find the frames that hold the time, or the retainer chain for a leak.
3. Map the frame to a file and a symbol. A frame with no source map is not yet a diagnosis.
4. If you have a paired before and after, diff them. Otherwise label the finding as the strongest hypothesis the artifact supports.
5. Hand back the cited diagnosis. Do not start a fix unless the brief asks.

Apply the boundaries in `../SKILL.md`. Do not spawn subagents, pick a model, install a hook, or run an upstream script.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
