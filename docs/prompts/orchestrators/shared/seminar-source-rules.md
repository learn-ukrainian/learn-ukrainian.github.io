# Shared Seminar Source Rules

Prompt suite component version: 0.2
Last reviewed: 2026-06-22

Use these rules for seminar tracks such as FOLK, HIST, BIO, LIT, active LIT subtracks, ISTORIO, OES, and RUTH. Adapt them to the target track; do not copy core CEFR assumptions into seminar work.

## Active Track Taxonomy

- Verify active track names from the current repo before writing prompts or modules.
- Prefer active source/site directories and `curriculum.yaml` over stale plan-only leftovers.
- Do not create prompt suites for plan-only remnants such as `lit-crimea` or `lit-doc` unless the current curriculum and site manifest say they are active tracks.
- For LIT work, create separate prompt suites for the active `lit` and active `lit-*` tracks that exist in the current manifest. In the current taxonomy, `lit-youth` is the active children's/YA track; older docs may call the same planning area `LIT-JUVENILE`.

## Source Universe

- Treat the module plan, dossier, wiki/source registry, reading entries, and approved local RAG as the source universe.
- Do not invent titles, authors, collectors, publication dates, source IDs, or citations.
- For FOLK, inspect `docs/folk-epic/EXEMPLAR-STANDARD.md`, `docs/folk-epic/folk-review-rubric.md`, `docs/folk-epic/folk-text-layer-spec.md`, and `scripts/build/phases/linear-write-seminar-folk-rules.md`.
- For later seminar tracks, inspect the closest track-specific audit and rubric files before adapting FOLK rules.
- Use `docs/prompts/orchestrators/shared/seminar-track-checklists.md` for track-specific source families and high-risk checks before adapting FOLK rules.
- For historical-linguistic tracks OES and RUTH, treat source passages, orthography, paleography, register, and terminology as factual content. Do not use "Old Russian" or "Common East Slavic" framing where the track docs require Old Rus' / Old Ukrainian / Ruthenian terminology.

## Quote And Claim Integrity

- Every verbatim primary text fragment needs provenance: exact source, author/collector where known, and verification status.
- FOLK verbatim song, duma, proverb, or ritual fragments must be verified against repo-supported source tooling or marked do-not-quote/paraphrase-only.
- Never quote from memory. Never smooth archaic, dialectal, or original spelling inside a verbatim quote.
- Teacher prose around a quote must use modern, VESUM-clean Ukrainian unless the term is explicitly verified as heritage/regional vocabulary.
- Extraordinary claims need explicit source support. Wikipedia-only claims can provide orientation but must not override corpus, dossier, named edition, or source registry evidence.

## Decolonization And Bias Checks

- Check for Russocentric framing, imperial inheritance, appropriation laundering, Soviet distortions, and romantic-nationalist overclaiming.
- Name contested framing when the evidence is contested; do not turn disputes into settled facts.
- Surface Ukrainian agency and regional variation without flattening the material into a single national myth.
- Record antisemitic, xenophobic, colonial, or otherwise harmful historical content honestly when source-grounded, with learner-safe framing and no euphemistic laundering.

## Seminar Pedagogy

- Seminar modules should feel like guided source work: primary text first, close reading, source criticism, competing interpretations, and a defensible argument.
- Avoid encyclopedia voice and generic content recall. Ask what the source permits the learner to infer.
- Activities should practice reading, source evaluation, comparison, interpretation, argumentation, and seminar discussion.

## Review Requirements

- Require independent-family review before merge.
- Treat unresolved factuality, quote integrity, ghost-source, reading-link, copyright, or decolonization findings as blockers.
- The review must cite files, lines, source IDs, or exact reading entries. A generic "looks good" review is not enough for seminar tracks.
