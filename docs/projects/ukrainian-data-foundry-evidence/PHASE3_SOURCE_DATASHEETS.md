# Phase 3 source-family datasheets

These datasheets describe the source families represented by the Phase 3
stand-off product. They are operational evidence boundaries, not universal
legal opinions. The binding per-source capability decisions and evidence
references remain in the Phase 2 complement.

## Literary

- **Records:** 137,723.
- **Phase 3 representation:** revision-pinned source/work locator, source axes,
  content/context hashes, and whole-record stand-off offsets.
- **Published text:** none from the Phase 2 family.
- **Use:** local alignment, conservative historical/heritage protection, and
  source-controlled candidate generation.
- **Limitation:** metadata can protect or route a whole record but cannot prove
  a span-level correction.

## Public textbooks and reference works

- **Records:** 49,193.
- **Ministry-track school-edition records:** 48,996, distributed across grades
  1–11.
- **Reference-work records:** 197 with no school grade. These are 169 pages of
  Borys Antonenko-Davydovych's *Як ми говоримо* and 28 pages of Mykola
  Pohribnyi's *Українська літературна вимова* (1992).
- **Important classification note:** the two reference works share the
  historical `public_textbooks` storage family but are not Ministry school
  editions. Consumers must not describe all 49,193 rows as school textbooks.
- **Published text:** none from the Phase 2 family; Phase 3 publishes stand-off
  locators and evidence only.
- **Use:** local source alignment, register/context evidence, and cited
  correction/protection rules where the separate evidence gate passes.

## External articles and transcripts

- **Records:** 1,205.
- **Phase 3 representation:** canonical source/work locator, revision/content
  hash, source axes, and stand-off offsets.
- **Published text:** none.
- **Use:** locally controlled contextual inspection and conservative routing.
- **Limitation:** source availability and publication capability remain
  per-source decisions; a family label does not grant redistribution.

## Ukrainian Wikipedia

- **Records:** 1,029.
- **Phase 3 representation:** canonical URL, revision/content hash, source axes,
  and stand-off offsets.
- **Published text in this product:** none. Phase 3 remains conservative even
  where another separately controlled product may have a broader capability.
- **Use:** revision-aligned local processing and modern/reference context.
- **Limitation:** attribution, share-alike, modification notice, license notice,
  and no-additional-restrictions obligations remain downstream requirements.

## Project-authored public canaries

- **Records:** 99 sources/cases with 245 evidence records.
- **Published text:** short project-authored contexts only, under explicit
  publication evidence.
- **Use:** public known answers, consumer examples, mutation tests, and the
  non-erasure harness.
- **Learning status:** always false. They are public canaries, not training rows
  and not a held-back equivalent.

## Coverage and rights summary

The full release publishes 189,150 source-blind Phase 2 stand-off candidates
and 99 public canaries. A non-redistributable source remains usable because a
consumer can align its lawful local copy with `source_id`, `work_id`, revision
pin, content hash, and offsets. Source text or a derived span is published only
for the project-authored canaries whose exact capability is evidenced.

The machine-readable counts, category gates, evidence grades, disagreement,
periods, genres, registers, and dispositions are in
`data/projects/open_model_data/release/correction_protection_v1/coverage.json`.
