# Heritage pairs: reviewed growth and delivery

**Scope:** #6140 · parent #6132 · umbrella #4387

`registry/lexicon/heritage_pairs.yaml` is the reviewed source of truth for the
Heritage practice mode. A pair is a practice item only when its native slug
resolves to a public practice lexeme and it has a source, an authored frame,
and an explicit severity. This prevents raw corpus suggestions from becoming
learner-facing corrections.

## Review path

| Source layer | What it establishes | Pair admission rule |
| --- | --- | --- |
| Antonenko-Davydovych and State-Standard textbook citations collected in `scripts/lexicon/calque_corrections.py` | A reviewed correction and its sense restriction | Copy the cited correction only after the native lemma resolves in the public Atlas and add a project-authored frame. |
| UA-GEC v2 `F/Calque` gold evidence (`registry/ua-gec-gold/ua-gec-gold.json`) | An annotated source → correction pair under CC-BY-4.0 | Keep the exact UA-GEC ID in `citations`; do not treat a raw frequency row as an independent correction. |
| Atlas `heritage_status` / `is_russianism` | Additional evidence when the calque itself has an Atlas entry | Use it to support severity, never to override a sense restriction or invent a replacement. |

The 2026-08-03 batch grows the source from 72 to 90 pairs. Its additions are
the 15 rows whose native counterparts already resolve from
`CURATED_CALQUES`, plus the direct UA-GEC gold pairs `3091`, `3106`, and
`3352`. Candidate rows without a resolvable public native practice lemma,
only a phrase replacement, a morphology-only correction, or insufficient
sense evidence remain candidates rather than cards.

## Build-time gates on calque judgments and explanations (#8727, #8728)

The factory withholds, with a `WARN … withheld` line on stderr, any pair or
item that fails one of these checks. Withheld records stay in the YAML; a
curator repairs the evidence, never the gate.

| Gate | Rule | Repair |
| --- | --- | --- |
| Normative support (`_heritage_normative_support_error`) | A pair whose `citations` are only corpus counts (`ua-gec:…`) is emitted only when VESUM has no clean analysis for its `calqueLabel` and every `calqueSurfaces` entry, i.e. the calque itself is not a standard form. A clean VESUM word backed by a single annotator correction (`вибачення` → `вибачити`, n=1) is not a calque judgment. | Add a normative citation (Антоненко-Давидович, State Standard, dictionary, textbook chunk) verified with the `sources` tools, or leave the pair withheld. |
| Frame calque identity (`_heritage_frame_calque_mismatch`) | Each frame's `calque_form` must be a form of the pair's calque: exact surface, VESUM lemma, or a shared stem when VESUM cannot analyse one side. A frame for another word (`настільки` under `да → так`) would inherit a copied rationale. The overlay merge in `read_heritage_pairs` applies the same test, so a wave row's frames only join a curated pair when they share its calque. | Give the frame its own pair with its own rationale and citations. |
| Explanation language (`explanation_language_errors`) | Every Cyrillic token of a learner-facing explanation (`rationale`, `rationaleUk`, `calqueSense`, `authenticSense`, and `distinction_gloss_uk` for paronym, antonym and homonym items) must be a clean VESUM form. Quoted mentions («…») and `рос. …` spans, the item's own contrasted forms, and dictionary abbreviations written with their period are exempt. | Replace the word with wording copied from a verified source; never paraphrase by hand. `--broken-validator-fixtures` proves the gate on a planted «вежливий». |

### Measured effect (2026-09-27, same `atlas.db`/VESUM inputs, `--disable-cloze`)

| mode | level | origin/main generator | gated generator |
| --- | --- | --- | --- |
| heritage | A1 / A2 / B1 / B2 / C1 | 7 / 44 / 265 / 26 / 12 | 4 / 24 / 105 / 14 / 11 |
| paronym | A1 / A2 / B1 / B2 / C1 | 35 / 44 / 138 / 33 / 6 | 32 / 43 / 137 / 33 / 6 |

The heritage loss is 123 pairs (130 build-time withhold lines) whose only
evidence is a UA-GEC count while VESUM analyses the calque as a clean form or
cannot analyse a multiword calque («так як», «в якості», «в першу чергу»), plus
five frames whose calque is a different word. Eight of the withheld pairs carry
`severity: russianism` («но», «надо», «пол», «стакан», «залив», «сідий»,
«тьотя», «любий»): their calque is a VESUM homograph of a real Ukrainian word,
so the gate cannot clear them from VESUM alone and they need a verified
normative citation to return. The explanation gate withheld 3 heritage, 10
paronym and 22 homonym items, all on VESUM `:bad` forms (active participles
such as «існуючий», «діюча»; «доставки», «прийому», «поліцейського»,
«торговельна») or one unknown form («начесом»).

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
