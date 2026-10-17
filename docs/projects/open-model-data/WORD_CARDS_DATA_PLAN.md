# Epic #6321 — word-card data, dataset-first (plan v1.2)

Status: APPROVED — designated approval: author Claude Opus 5.5 (open-model-data driver), GPT-6.1 Sol APPROVE on v1.1
(`design-cards-plan-sol-r2`, sha256 0dd10f0d…) after v1 REQUEST_CHANGES (`design-cards-plan-sol`; §8 maps each finding).
v1.1.1: editorial — §7 ВТС residual reworded to match §6 (the one non-blocking residual of round 2). v1.1.2: §7 duplicate ВТС entry removed (doc-review residual).
v1.2: execution policy. The existing Atlas backed by atlas.db remains live. Improving and publishing that Atlas
proceeds now, separate from the later switch of Atlas pages to word-card records. The Atlas lane owns presentation
and publication; the open-model-data lane owns card and data work. This amendment neither deploys nor certifies
anything. Detail: §9.
Authority: operator decisions 2026-10-06 on #6321 — (1) word-level dataset components come from the word cards,
superseding RB-1 design §6(b); (2) the open-model-data lane owns word-card DATA end to end, the Atlas lane keeps
presentation. No deadline ("no drift, no rush").

## 1. What changes and what does not

- **Unchanged:** the card design — `docs/atlas/word-cards/schema.md` (spec r3 + r4/r5 fixes), `identity.md`,
  `migration.md` gates (Gate 1 pilot, Gate 2 golden set with a sealed held-out pool), the foundation
  (`scripts/atlas/word_card_foundation.py`: `freeze`/`allocate`/`verify`), the frozen pilot
  (`registry/atlas/pilot/pilot-v1.json`, 150 units) and its 114 allocated identities
  (`registry/atlas/identity/registry.json`). RB-1 P1–P6 and its gate (§4) are unchanged.
- **Changed:** order and first consumer of word-card records. This plan builds the card fields the dataset
  needs first, from held sources only (M3 "re-extract, do not copy"), with the dataset projection (#8988)
  as the first card consumer. Atlas pages and practice consume those cards later, and only through the
  switch gate in §9. The existing Atlas backed by `atlas.db` stays live: the Atlas lane improves and
  publishes that Atlas now. That current delivery is separate from the dataset release and from the later
  switch to word-card records. `migration.md` still starts from today's `atlas.db` as the page baseline
  the cards must meet; it does not park current `atlas.db` improvements.
- **RB-1 components:** C2 (forms, stress), C3 (synonyms/antonyms by sense, СУМ-20 meanings), C4 (phraseology) and
  C7 (Russification contrast) become projections of the cards. C1, C5, C6, C9 continue directly (REVIEW_BUILD.md
  v1.4 records this; §6(b) is withdrawn).

## 2. Ownership (operator decision)

| Data lane (this epic) | Atlas lane (#4387) |
| --- | --- |
| card store, ingestion (ULIF, VESUM, СУМ-20, phraseology, PULS, …), identities and registry events, citations, sense binding, suppression/takedown (#8980), the Russification data model and gate (#8982 AC-01/AC-03), field gates, dataset projection (#8988, #8989), Gate 1 data checks, Gate 2 golden set | Atlas pages, practice eligibility and decks (#8983, #8984), site, the reviewed Atlas page section for Russification (#8982 AC-02), lesson links |

Current `atlas.db` presentation and publication proceed now under the Atlas lane. Card and dataset work
stay with this lane. Switching Atlas pages to word-card records waits for §9.

Issue membership moves after the Atlas lane replies (msgs 261/262; default 2026-10-06T14:00Z).

## 3. The slice: fields and their acceptance rules

The dataset's binding rules become card **acceptance rules**. **Normative source:** the frozen RB-1 component
specifications (REVIEW_BUILD.md §4–§5), the reviewed catalog applicability and each component's closed reason list;
the table below is a summary and never replaces them. The card store keeps **evidence** (every source unit, with its
disposition) separate from **accepted facts**: a held or withheld unit stays in the store with its reason code and
never counts as accepted, aligned or eligible. The projection re-checks every accepted fact (P5) over citation
identities. Every assertion carries
`source_id`, `snapshot_id`, `locator`, `licence_ref`, `extraction_version` (schema §3–§4, §10).

| Field (schema) | Sources | Acceptance rule (from the reviewed RB-1 work) | Reused work |
| --- | --- | --- | --- |
| `paradigm` (forms per slot) | ULIF (primary, stressed), VESUM (supporting; version from `vesum_source.lock.json`) | a slot's form set is accepted only when VESUM's form set for the same lexeme and slot equals ULIF's (all variants), with the source sense/template applicability of the C2 spec; omission classes keep their reason codes (asterisk, preposition-bound, unmapped label, unauthenticated header cell, the failed entries, parse-error homonym groups, homonym unbridgeable) | WP2 extractor + census, branch `codex/impl-rb1-wp2c` @1fbfbe98 |
| `stress` | ULIF stressed forms; `ukrainian_word_stress` lineage | scalar with `variant` vs `conflict` (schema §8); conflict never auto-resolved | WP2 |
| `senses[]` + `definition_uk` | seed (§6 decision 1): an unquarantined СУМ-20 article **mapped to this lexeme** (22,075 cached entries), else ВТС numbered senses **(admitted source round 2026-10-17; 31,688 cached entries)** (§6), else ULIF `sense_gloss` units (47,050 glossed entries); an entry with no nonblank gloss keeps one `unsplit` sense with no meaning; sense ids are preserved when a richer source arrives | definitions verbatim from unquarantined СУМ-20 senses (89 articles / 168 senses today in sources.db; 22,075 in local cache), labels and the sense's own citations bound to the same article and sense; the 11 quarantined articles never appear (#9609, #9840) | WP3 СУМ-20 meaning |
| `synonyms`/`antonyms` by sense | ULIF synonym/antonym sections | members bound to one `sense_or_group_id` of the same entry; a multi-group entry without a source-visible discriminator is **withheld** `sense_not_visible` (806 sections in WP3) — kept as evidence, never accepted, never assigned by position; a source-readable group discriminator is not alignment to a seeded card sense (schema §6: automatic alignment only when both sides have exactly one unit); «рада» wrong-homonym fixture must fail | WP3, branch `codex/impl-rb1-wp3c` @bdf70eda (69,714 / 469 accepted in RB-1 terms) |
| MWE cards (idioms) | ULIF phraseology sections; Фразеологічний словник only with an edition record (#9609) | an identifiable printed idiom ↔ a nonempty definition ↔ author-labelled citations, all from one section (withheld: `sense_not_visible`, `definition_unresolved`, `citation_unresolved`); component links via ULIF anchors (schema §7.1) | WP3 phraseology (3,385 accepted) |
| `russification_exposed` (sense) | Антоненко-Давидович pairs adjudicated by two seats; СУМ-11 as `soviet_colonization_context` only | contrast-pair identity = the cited Антоненко row **plus its two-seat adjudication receipt**; both form spans cited; СУМ-11 binds to the rejected form (with `sovietization_risk` and keywords), ULIF + VESUM to the recommended form; swapped recommendation fails; opt-in export only; never a definition, stress, example or answer (schema §14) | WP6 C7 extractor, branch `codex/rb1-wp6-c7-card-input`; 637 agreed + ≈ 240 reconciled pairs |

Out of this slice: `english_gloss`, `cefr` (#9845, later), `examples`, `collocations`, practice eligibility.

## 4. Milestones (each: denominator, proof, review)

Denominators are frozen at the source-unit grain of each field: ULIF (entry, slot) for forms/stress, relation
sections for synonyms/antonyms, СУМ-20 sense rows for meanings, phraseology sections for idioms, Антоненко rows for
contrast pairs. Every unit ends in exactly one disposition (accepted, held, withheld:<reason>, excluded:<reason>).

- **W0 Handover and held-out freeze.** Issue membership moved; lane slots (#9854); RB-1 design v1.4;
  #9820/#9821/#9823 re-scoped. **Before any development on cards:** freeze the Gate 2 held-out membership
  (migration §4: 220 cases, 40 % held out, disjoint) so no development or overlay adjudication touches it.
  Proof: issue-stream audit; held-out manifest SHA recorded; the overlay loader refuses held-out keys (test).
- **W1a Vertical slice (lesson from RB-1: prototype first).** 4–6 existing pilot units covering ordinary
  agreement, a homonym ambiguity, a multi-sense word and an idiom, end to end: ingestion → assertions → card →
  projection → RB-1 gate. Proof: rebuild byte-identical; every locator resolves read-only; per-unit dispositions.
- **W1b Card store + assembly on the pilot (#9402).** The schema §15 store and `build(S,V,I,O,R)` for the slice
  fields over the 150 frozen pilot units; WP2/WP3 code behind the card extractor interface. Proof as W1a, plus
  per-field accounting conserving every unit. Review: the non-author frontier seat + Flash fixed-rubric checks.
- **W2 Forms disagreement root cause.** WP2 measured 46 % `form_set_disagreement` at ULIF scale. On the pilot,
  classify every disagreement (tag/slot mapping, variant spelling, VESUM gap, ULIF error, genuine) with tool
  quotes; fix mapping errors in the extractor; genuine disagreements stay `conflict`. Stop rule: > 10 % of pilot
  disagreements unexplained after one round → stop and redesign the comparison.
- **W3 Projection on the pilot (#8988).** C2/C3/C4 records projected from cards through the RB-1 framework.
  **Equivalence proof** against the direct WP2/WP3 extraction on the same units: candidate membership,
  dispositions, reason codes, cited values and bindings compared unit by unit; a lost record is a failure, not an
  "explained difference".
- **W4 Gate 1 data part.** M8 withdrawal / changed-snapshot / rollback rehearsal (#8980), M9 redirect and split,
  rebuild identity.
- **W5 Russification pilot (#8982 AC-01/AC-03).** Contrast-pair model and gate on the pilot cards (needed by the
  golden set's 15 Russification cases).
- **W6 Gate 1 complete.** Gate 1 passes only when the Atlas lane's part (rendering, applicable/ineligible practice
  combinations, generated-item semantic review, progress behaviour) also passes on the same pilot build.
  That check gates the card pilot. It does not hold current `atlas.db` publication (§9).
- **W7 Gate 2 golden set.** Implement the missing evaluation contract (today `verify --for-evaluation` refuses:
  no authenticated operator authority/signature or thresholds) — the operator signs the sealed manifest and sets
  the thresholds; two blind adjudicators outside the author's family; used held-out cases move to replay and are
  replaced.
- **W8 PULS A1–B1 coverage** (4,512 rows, migration §3 later obligation) for the slice fields.
- **W9 Full scale for the slice.** Only after W6 and W7. All ULIF entries for the slice fields; framework
  accounting streams (the WP2 full build hit MemoryError at 12 GiB — fixed and measured here). RB-1 C2/C3/C4 are
  then rebuilt from cards and enter D3; #8989 is projected from the W5 model at scale.

Order: W0 → W1a → W1b → (W2 ∥ W3 ∥ W5) → W4 → W6 → W7 → W8 → W9.

## 5. Constraints

No card data or dataset rows in the public repository beyond what the card design already commits (registry ids,
overlay, pilot manifests). **Card store placement:** generated stores stay host-only under the ignored `data/` tree,
as the card design allows. **Dataset output containment:** dataset files, logs, review inputs and receipts stay
outside every checkout under the RB-1 output guard (quarantine area); the two rules are separate. No scraping. Only the
operator contacts ULIF or UNLP. Ukrainian judgments: Claude, GPT or Gemini seats with the `sources` MCP; no
model-written Ukrainian in any card field.

## 6. Decisions this plan takes (driver, within approved design) and asks reviewers to check

1. **Sense seed.** СУМ-20 (unquarantined, mapped to the lexeme, 22,075 cached entries) → ВТС numbered senses (admitted for sense reference under Art. 22(2)(1) Law 2811-IX; numbered-sense extraction and card schema integration is an active engineering residual) → ULIF `sense_gloss` (47,050 glossed entries), as schema §16.3 item 2 recommends. Following the 2026-10-17 source admission round (`docs/sources/admissions/2026-10-17-vts-sum20-source-admission.md`), ВТС is admitted for card sense reference based on live Atlas practice (7,849 live entries; `definition_cards` parser in `scripts/lexicon/enrich_manifest.py`), slovnyk.me digital copy edition records (Бусел 2005/2009, 5-те вид., ВТФ «Перун»), and Art. 22(2)(1) Law 2811-IX educational quotation terms (`vts_busel_slovnyk_me` in `docs/sources/permissions-register.yaml`). Seeding is not semantic authority; cross-source sense counts are adjudicated through `sense_map`.
2. The pilot is the first denominator; full scale waits for the complete Gate 1 and Gate 2.
3. WP2/WP3 code is reused behind the card extractor interface rather than merged as RB-1 components.

## 7. Residuals and owners

C2 MemoryError (W9, this lane); 46 % form disagreement (W2, this lane); ВТС source admission completed 2026-10-17 (`docs/sources/admissions/2026-10-17-vts-sum20-source-admission.md`; numbered sense parsing and card schema integration remains an active engineering residual, W1a/engineering, this lane); acquisition of further authority books (#8791 closed by operator Decision A; Пономарів 2001 private reference only, remaining titles dropped);
#8334 identity/URL sign-off (Atlas URL part stays Atlas; identity part this lane).

## 8. v1 review findings → where v1.1 closes them (Sol, `design-cards-plan-sol`)
1. (blocker) `sense_not_visible` stays withheld; evidence vs accepted facts separated → §3 intro and table.
2. (blocker) ВТС is held locally; admission, not holding, decides → §3 senses row, §6 decision 1; blank-gloss fallback. (Source reference admitted 2026-10-17: permissions-register entry `vts_busel_slovnyk_me`, 31,688 cached entries; numbered-sense extraction/schema integration active residual under W1a).
3. (blocker) Full scale waits for the complete Gate 1 incl. Atlas checks, PULS coverage kept, Russification pilot
   before the golden set → W5, W6, W8, W9.
4. (should) Frozen component specs normative; C2/C4/C7 conditions added → §3.
5. (should) Held-out membership frozen before development; evaluation contract is W7 work → W0, W7.
6. (should) Vertical slice first; unit-grain denominators; unit-by-unit equivalence → W1a, §4 intro, W3.
7. (should) Card-store placement vs dataset output containment → §5.

## 9. Current Atlas delivery and the word-card page switch (v1.2)

The existing Atlas backed by `atlas.db` remains live. Improving and publishing that Atlas proceeds now.
That delivery is separate from the open dataset release and from the later switch of Atlas pages to
word-card records. The Atlas lane owns presentation and publication. The open-model-data lane owns card
and data work. This documentation amendment neither deploys nor certifies anything.

Programme Phase 5 certification and programme Phase 6 full coverage, as recorded on #8977, continue to
gate the open dataset release and the switch of Atlas pages to word-card records. Existing source, field,
provenance, licence, withdrawal, source-fidelity and certification obligations are unchanged. This
amendment does not reduce the source denominator, treat the pilot as gold, or accept uncertified cards
or exports. Dataset certification gates and licence gates are unchanged. The open-model-data driver
priority order remains #10512, then #8959, then #10853.

### Switch gate

Before Atlas pages switch from the current `atlas.db` pages to word-card records:

1. Freeze a lemma sample and both the current and candidate page and data versions. This plan does not
   set the sample size and does not certify that a switch has been executed.
2. Compare the current page and the candidate page side by side for every currently displayed field,
   for every sample member: forms, stress, senses, examples, citations. Examples stay in this comparison
   whether or not they are in the current card slice (§3).
3. The candidate must be equal or better on every one of those fields for every sample member. It must
   never carry fewer facts, and it must never carry a wrong form. Missing comparison evidence is not a pass.
4. Record the expected evidence, the current page evidence, the candidate page evidence, and any
   unresolved findings.
5. Independent cross-family review, and a Ukrainian-qualified check with source verification, are
   required before the switch.

Passing this comparison does not replace Phase 5 certification or full coverage. Editing this plan is
not the switch proof.
