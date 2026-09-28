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
curator repairs the evidence, never the gate. Source passages are read from
`data/sources.db` (`--sources-db`, the `sources` MCP database); without it
both source gates fail closed.

| Gate | Rule | Repair |
| --- | --- | --- |
| Normative support (`verified_source_passages`, `_heritage_frame_support`) | A calque judgment ships only with a `normativeSupport` entry: `locator` is a page chunk of a normative style guide listed in `HERITAGE_NORMATIVE_SOURCES` (today Антоненко-Давидович «Як ми говоримо», 1991 edition, `antonenko-davydovych-yak-my-hovorymo_pNNN`) and `passage` is copied verbatim from that page. Each frame ships only when the passage names that frame's calque and its correction (same form, VESUM lemma, or a shared stem when VESUM cannot analyse the calque). `citations` (UA-GEC counts, article titles, dictionary headwords, textbook names) are provenance notes and never admit a pair. The item's first learner-visible citation is the edition and page. | Copy the exact passage with the `sources` tools and check that its context matches every frame; otherwise leave the pair withheld. |
| Frame calque identity (`_heritage_frame_calque_mismatch`) | Each frame's `calque_form` must be a form of the pair's calque: exact surface, VESUM lemma, or a shared stem when VESUM cannot analyse one side. A frame for another word (`настільки` under `да → так`) would inherit a copied rationale. The overlay merge in `read_heritage_pairs` applies the same test. | Give the frame its own pair with its own rationale and support. |
| Paronym gloss provenance (`paronym_gloss_provenance_errors`) | `distinction_gloss_uk` ships only when it is copied from a `glossSources` passage (a Ukrainian-language school textbook chunk or a style-guide page, `PARONYM_GLOSS_SOURCES`) that is verbatim in its chunk. Each `<word> — <definition>` clause must be text the passage gives after that word and before its paronym (no swapped or paraphrased definitions), or the whole gloss must be one passage sentence naming both words. A de-interleaved reading of a two-column table is not verbatim text. | Copy a definition from a verified chunk; never paraphrase. A definition may stop early only at a phrase boundary. |
| Explanation language (`explanation_language_errors`) | Every Cyrillic token of a learner-facing explanation (`rationale`, `rationaleUk`, `calqueSense`, `authenticSense`, and `distinction_gloss_uk` for paronym, antonym and homonym items) must be a clean VESUM form. Only an explicit `рос. …` mention, the item's own contrasted forms (calque, answer, options, corrections) and dictionary abbreviations written with their period are exempt; quotation marks are not (`Тактовний — «вежливий»` is withheld). | Replace the wording with text copied from a verified source. `--broken-validator-fixtures` proves every gate on a planted defect. |

### Measured effect (2026-09-28)

Denominator: the published deck `atlas-practice-v1-c0c3f3242b5134b6`. The
regenerated deck (`atlas-practice-v1-9ab281221e5e0723`; same `atlas.db`,
VESUM and `sources.db`; `--disable-cloze`) retains an item when the same
prompt and answer still ship at any level.

| mode | level | published | retained | withheld | withheld by reason |
| --- | --- | --- | --- | --- | --- |
| heritage | A1 | 7 | 0 | 7 | 4 no normative passage, 3 frame calque is another word |
| heritage | A2 | 44 | 7 | 37 | 36 no normative passage, 1 frame calque is another word |
| heritage | B1 | 265 | 28 | 237 | 237 no normative passage |
| heritage | B2 | 26 | 9 | 17 | 17 no normative passage |
| heritage | C1 | 12 | 2 | 10 | 10 no normative passage |
| paronym | A1 | 22 | 4 | 18 | 18 gloss not source-linked |
| paronym | A2 | 17 | 6 | 11 | 11 gloss not source-linked |
| paronym | B1 | 69 | 27 | 42 | 42 gloss not source-linked |
| paronym | B2 | 11 | 4 | 7 | 7 gloss not source-linked |
| paronym | C1 | 5 | 1 | 4 | 4 gloss not source-linked |

Heritage keeps 24 pairs whose page-located Антоненко-Давидович passage gives
an explicit verdict in the sense every frame tests. Pairs were left without
support where the passage calls the word Ukrainian («дійсно»), gives no verdict
on a form standard today («крокувати»), discusses another sense than a frame
(«благополучна родина» vs «благополучна посадка»), or where no single page
names both forms («знаходитися → розташований», «облік → обличчя»). Paronym
keeps 24 rows whose explanation is now copied from a school textbook or
style-guide chunk. The withheld rows and pairs stay in the registries and
return when a curator adds a verified passage (replacement work: #8329).

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
