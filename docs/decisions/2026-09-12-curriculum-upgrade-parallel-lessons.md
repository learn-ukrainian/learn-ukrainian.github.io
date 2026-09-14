# Curriculum upgrade: canonical lessons and the archived A1 edition

Status: operator GO revised on 2026-09-12; implementation in #7994 / draft PR #7999.

Option A publishes each 60-minute lesson at `/{level}/{slug}/{n}/`, under a
module landing at `/{level}/{slug}/`. Each page has the V7 four tabs. The landing
provides objectives, lesson cards and linked aggregate vocabulary, practice and
resources. The final lesson closes the module; vocabulary knowledge advances per
lesson.

The later operator GO supersedes the morning parallel-preview naming decision:
we will not rebuild the old modules. Archive the existing 55-module edition and
its built single-page MDX under `a1-v1` (`base_level: a1`). Canonical `a1` is the
upgraded lesson edition, with no base-level alias. Plans remain in `plans/a1/`.

The PR performs the archive move without rebuilding. Canonical A1 lists only
published upgrades, initially none because live writers are not authorized here.
Old `/a1/{slug}` bookmarks fall back to `/a1-v1/{slug}` until a published lesson
landing exists; then the new canonical landing wins. No handmade Phase 0 lessons
are product content. Keep PR #7999 draft: merging would change live `/a1/` URLs;
merge, undraft and deployment remain unauthorized.
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
