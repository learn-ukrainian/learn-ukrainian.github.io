# Heritage pairs: reviewed growth and delivery

**Scope:** #6140 · parent #6132 · umbrella #4387

`data/lexicon/heritage_pairs.yaml` is the reviewed source of truth for the
Heritage practice mode. A pair is a practice item only when its native slug
resolves to a public practice lexeme and it has a source, an authored frame,
and an explicit severity. This prevents raw corpus suggestions from becoming
learner-facing corrections.

## Review path

| Source layer | What it establishes | Pair admission rule |
| --- | --- | --- |
| Antonenko-Davydovych and State-Standard textbook citations collected in `scripts/lexicon/calque_corrections.py` | A reviewed correction and its sense restriction | Copy the cited correction only after the native lemma resolves in the public Atlas and add a project-authored frame. |
| UA-GEC v2 `F/Calque` gold evidence (`data/ua-gec-gold/ua-gec-gold.json`) | An annotated source → correction pair under CC-BY-4.0 | Keep the exact UA-GEC ID in `citations`; do not treat a raw frequency row as an independent correction. |
| Atlas `heritage_status` / `is_russianism` | Additional evidence when the calque itself has an Atlas entry | Use it to support severity, never to override a sense restriction or invent a replacement. |

The 2026-08-03 batch grows the source from 72 to 90 pairs. Its additions are
the 15 rows whose native counterparts already resolve from
`CURATED_CALQUES`, plus the direct UA-GEC gold pairs `3091`, `3106`, and
`3352`. Candidate rows without a resolvable public native practice lemma,
only a phrase replacement, a morphology-only correction, or insufficient
sense evidence remain candidates rather than cards.

## Severity and level guidance

Every pair has one of two textual learner-facing values:

- `russianism` — direct Russian-calque / surzhyk evidence or an explicit
  Atlas classifier citation; the feedback is firm in the frame's stated
  sense.
- `enrichment` — a reviewed alternative or sense-limited doublet where the
  frame teaches a richer native choice without treating every use of the
  other form as wrong.

The initial migration uses those directly recorded signals in the pair's
citations, rationale, and curator notes. It deliberately does not infer
severity from spelling or a raw `russian_shadow` flag.

`cefrAvailability` is curator guidance, not a global hard exclusion. It may
be `a1`, `a2`, or `b1`; omitted guidance retains the B1 default. The factory
places a card no lower than both the native lexeme's level and the curator's
explicit guidance. Consequently, an easy native can be admitted at A1 without
lowering unrelated B1 cards. Two existing, source-backed everyday pairs,
`да → так` and `папа → тато`, are curator-admitted to A1. The new
`головуючий → голова` pair remains B1 because its meeting context is not A1
practice, and `удалився → пішов` remains A2 with its motion sense restricted.

## Factory and release path

1. Validate the YAML and native lexeme resolution with the practice-deck tests.
2. Run `make practice-deck` after hydrating the Atlas manifest and supplying
   the explicit VESUM shadow database required by the factory.
3. Inspect `site/public/lexicon/practice-heritage.{level}.json`; count the
   A1 cards and the emitted `severity` values.
4. Run `make practice-deck-publish` only after the generated shards and their
   expected deck version agree. It uploads the immutable release asset and
   updates `site/src/data/lexicon-practice-deck.pointer.json`.
5. Hydrate the practice package for a local user-visible smoke test; the
   pointer, rather than local shards, is the deployed source.

`site/public/lexicon/` is generated and may be absent from a sparse checkout.
Never hand-edit a shard or a release pointer to make these numbers change.
