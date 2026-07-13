# Seminar semantic post-build review prompt

Semantic prompt version: `2.0.0`

Apply this only to FOLK, HIST, BIO, ISTORIO, LIT and subtracks, OES, or RUTH,
after the common prompt.

## Exhaustive claim ledger

Extract every checkable factual claim into `claim_ledger` as an atomic item:
people, dates, places, events, works, categories, typologies, periods,
etymologies, quotations,
attributions, causal claims presented as fact, image/rights claims, and source
claims. Verify every item. Derive total, checked, and supported counts from the
ledger. Any unchecked item makes claim coverage incomplete.

Classify every ledger item as supported, contradicted, imprecise, unattested,
or unverifiable and give attributable evidence. Do not emit aggregate counts
without the ledger that proves them. A contradicted teaching claim is a blocker. Confidently
specific but unattested material is at least high and may be a blocker when a
named source/person/event should be findable.

## Track-sensitive judgment

- Center Ukrainian agency and Ukrainian scholarly categories. Detect Russian-
  imperial, Soviet, common-heritage, colonial, and Western-centrist framing.
- Distinguish evidence from interpretation, and interpretation from praise.
  Reject hagiography and unsupported moral/psychological narratives.
- For BIO, verify education, roles, relationships, chronology, works, awards,
  repression/recognition claims, quotations, and image rights. Do not treat
  Oleksandr Bilash's headings, length range, works, or final disposition as a
  global BIO template.
- For literary and historical-language tracks, verify textual evidence,
  edition/source identity, dating, genre, and anachronism risks.
- For FOLK, enforce decolonized framing and distinguish documented practice
  from occult belief claims or demonizing ethnographic language.
- Distinguish source-backed exposition and necessary primary readings from
  authored padding. Quoted refrains are not repetition; repeated authorial
  framing, conclusions, transitions, or definitions without new evidence are.
- Set `claim_coverage.status` to `complete` only when every extracted claim was
  checked with attributable evidence.
- Build `learner_evidence_ledger` for every reading, listening, viewing, image,
  or interactive task. Exact auditory/visual timestamps, transcriptions,
  perceptual descriptions, and model answers require direct modality-capable
  verification. A page title or catalog metadata never verifies the media
  content behind it.
