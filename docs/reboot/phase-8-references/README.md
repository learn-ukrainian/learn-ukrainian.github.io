# Phase 8 references — preserved manually-anchored material

> **Purpose:** When the EPIC #1577 reboot reaches Phase 8 (literacy
> bootstrap — A1/1, A1/2, A1/3), this directory holds hand-crafted,
> source-anchored Ukrainian curriculum material that predates the reboot
> and would otherwise be lost.
>
> **Status:** REFERENCE ONLY. Not part of any active build pipeline.
> Phase 8 may use these as input, ignore them, or supersede them — that
> decision belongs to whoever drives Phase 8.

---

## What's here

### `sounds-letters-and-hello-module.md` (104 lines)

Hand-written Ukrainian module prose for **A1/1 — Звуки і літери** (the
literacy bootstrap module). Source-anchored to real textbooks:

- Заболотний 5 клас, p. 83 — звуки vs літери rule
  («Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо»)
- Большакова 1 клас, p. 24 — vowel-introduction verse
- Літвінова 5 клас, p. 130 — голосна-літера terminology question
- Bartenev / Levenets / Vashulenko (across the knowledge packet)

Content covers звук-vs-літера distinction, the 33-letters-vs-38-sounds
rule, four exception classes (iotated vowels, Ь soft sign, Щ=шч,
phonetic spelling principle), and the introduction to голосні звуки.

Includes `<!-- VERIFY -->` markers showing source-checking discipline
applied during authoring.

### `sounds-letters-and-hello-knowledge-packet.md` (~1.2 KLOC)

The research/RAG knowledge packet that fed module authoring: textbook
excerpts, dictionary entries, decolonization notes, prior-art links.
The Phase 8 writer (whichever agent is chosen) can re-use the same
research packet rather than re-running the retrieval step.

---

## Provenance

Originally lived in `.worktrees/verify-a1-1-phaseA-v5/` on branch
`verify/a1-1-phaseA-v5`. That branch was part of EPIC #1550 (a1/1
verification on the v5/v6 pipeline) — the pre-reboot verification
pass that ran into the early reboot decision (2026-04-25 evening,
`docs/session-state/2026-04-25-evening-reboot-decision.md`).

The branch's commits all merged to main; the worktree retained these
two files as uncommitted work-in-progress. With the reboot superseding
v5/v6 entirely, the worktree was due for cleanup. These two files were
the only material with durable value — pipeline-specific artifacts
(activities YAML, audit reports, review files, MDX) were correctly
deleted as v5-era.

Preserved 2026-04-26 by Claude (late-evening session) before removing
the v5 worktree. See `docs/session-state/2026-04-26-qg-bugfix-shipped.md`
for that session's context.

---

## How Phase 8 should treat these

Three reasonable approaches (Phase 8 driver picks):

1. **Use as input.** Feed the module prose to the Phase 8 writer as a
   "v5 baseline — improve from here" reference. Source anchors are
   already done; the writer focuses on integrating with the new
   contract / immersion ratio / activity schema.

2. **Use the knowledge packet only.** Skip the module prose; feed the
   knowledge packet to the writer as research context. Lets the writer
   produce fresh prose with the same source grounding.

3. **Ignore entirely.** Phase 8 starts from the reboot's Lesson Contract
   + North Star and writes from scratch. Reasonable if the reboot's
   pedagogy diverges enough from the v5 approach that the prose is more
   distraction than help.

The 104-line module prose is *worth reading even if discarded* — it
demonstrates source-anchored Ukrainian curriculum authoring discipline
that the reboot should match.

---

## Not preserved (discarded as obsolete)

For the record, the v5 worktree also had these uncommitted changes
that were correctly NOT preserved:

- Deletions of `activities/sounds-letters-and-hello.yaml`,
  `audit/...`, `review/...-r{1,2,3}.md`, `status/...json`,
  `vocabulary/...yaml`, `starlight/.../sounds-letters-and-hello.mdx`
  — all already gone from origin/main; the worktree's "deletions"
  were no-ops aligning with upstream.
- `build-stats.jsonl` modifications — pipeline telemetry from v5
  build runs; not curriculum content.

The branch `verify/a1-1-phaseA-v5` itself had no unique commits at
removal time (all 5 commits already on origin/main). Branch deleted
as part of the same 2026-04-26 cleanup.
