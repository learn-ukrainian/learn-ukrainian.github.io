# Curriculum upgrade: parallel lessons under a module landing

Status: operator decided, 2026-09-12; implementation tracked in #7994.

Option A publishes each 60-minute lesson at `/{level}/{slug}/{n}/`, under a
module landing at `/{level}/{slug}/`. Each page has the V7 four tabs. The landing
provides objectives, lesson cards and linked aggregate vocabulary, practice and
resources. The final lesson closes the module; vocabulary knowledge advances per
lesson.

The first parallel level is `a1-v2`, pedagogically aliased to A1. Current A1
remains live and untouched; archive and cut-over require a later decision/action.
Upgrade mode extends V7 using the existing built artifacts, preserving original
prose and activity structure while expanding teaching support. No wiki packet or
plan rewrite occurs. Phase 0 #7991 is held-out evidence, not pipeline output.

No named narrator or self-introduction is used. Named people belong in dialogues.
Quotations require visible attribution and a Resources entry; reference authors'
personas and lesson structures are not adopted. Stress annotation follows review
and its correctness is gated against the existing oracle.

See [Phase 1 spec](../epics/curriculum-upgrade-phase1-spec.md) for schemas,
acceptance, non-goals and remaining decisions. This record records the operator's
existing choice; it does not authorize new pedagogy, skill edits, merge or deploy.
