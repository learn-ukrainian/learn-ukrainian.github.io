# Decision: lexicon explains; practice decks drill

- **Date:** 2026-07-28
- **Status:** accepted (operator GO 2026-07-28)
- **Parent:** #4387
- **Related:** #5793, #5792, #5910, #5917, #5918, ADR-017

## Decision

1. **Lexicon / Word Atlas explains a word.** It is dictionary-like: senses,
   English gloss, morphology, and, where appropriate, a source-located,
   rights-resolved attestation or a short dictionary-style example. This is
   the same explanatory role as an official lexicon.
2. **Practice decks drill a word.** Clozes, SRS, deck membership, distractors,
   and pedagogical example lines belong to the practice deck, practice seed, or
   deck-item SSOT. A deck item references a sense and may optionally reference
   an attestation.
3. **Do not mix the inventories.** Practice sentences must not be accumulated
   in lexicon entries merely because practice needs them. That inventory is
   unbounded and would corrupt both products. Reuse occurs by pointer—deck item
   to sense or attestation—not by copying the practice inventory into the
   article.
4. **Enrichment and QG reuse is library-level.** VESUM, deterministic Hramatka
   QG helpers, and eval-harness morphology checks may be shared libraries, with
   separate rule packs for decks and lexicon. The Hramatka lesson pipeline is
   not the lexicon writer.
5. **ADR-017 ownership remains explicit.** `attestations` are not authored
   practice examples, while `practice_deck_items` own deck linkage.

## Consequences

- Lexicon entries remain bounded explanatory articles instead of becoming a
  practice-bank mirror.
- Practice authors own pedagogical sequencing, item wording, and distractors
  where those concerns belong.
- Shared linguistic validation can improve both products without collapsing
  their editorial responsibilities.

## Non-decisions

- This does not forbid a lexicon article from displaying a cited attestation
  that a deck also uses.
- This does not freeze #5910's `make curated-v5-admit` transitional factory; the
  end-state ownership remains split.

## Evidence

- Operator GO, 2026-07-28.
- [ADR-017: Atlas projection schema and lifecycle](../architecture/adr/adr-017-atlas-schema-and-lifecycle.md), especially its distinct `attestations` and
  `practice_deck_items` records.
