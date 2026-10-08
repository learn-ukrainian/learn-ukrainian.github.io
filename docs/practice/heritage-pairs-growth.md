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
| Normative support (`verified_source_passages`, `_heritage_frame_support`) | A calque judgment needs a `normativeSupport` entry: `locator` is a page chunk of a normative style guide listed in `HERITAGE_NORMATIVE_SOURCES` (today Антоненко-Давидович «Як ми говоримо», 1991 edition, `antonenko-davydovych-yak-my-hovorymo_pNNN`) and `passage` is copied verbatim from that page. Each frame also needs a `normativeJudgment`: `endorsedForm` equals its `answer_form`, `rejectedForm` equals its `calque_form`, `sense` is nonempty, `locator` matches the verified passage, `passageSha256` binds that passage, and `sentenceSha256` binds the frame's `sentence_with_slot`. The passage must name both forms (same form, VESUM lemma, or a shared stem when VESUM cannot analyse a form). Form occurrence alone does not establish the correction's direction or sense. `citations` are provenance notes and never admit a pair. The item's first learner-visible citation is the edition and page. | Copy the exact passage with the `sources` tools; review its direction and sense against each frame, then record the judgment and digests below. A missing or mismatched judgment withholds the frame. |
| Frame calque identity (`_heritage_frame_calque_mismatch`) | Each frame's `calque_form` must be a form of the pair's calque: exact surface, VESUM lemma, or a shared stem when VESUM cannot analyse one side. A frame for another word (`настільки` under `да → так`) would inherit a copied rationale. The overlay merge in `read_heritage_pairs` applies the same test. | Give the frame its own pair with its own rationale and support. |
| Paronym gloss provenance (`paronym_gloss_provenance_errors`) | `distinction_gloss_uk` needs a `<word> — <definition>` clause for **each** contrasted word. Each definition must appear after its own word and before the other word in a verified, source-located `glossSources` passage (a Ukrainian-language school textbook chunk or a style-guide page, `PARONYM_GLOSS_SOURCES`). The words may have separate passages. A swapped or paraphrased definition, or a de-interleaved reading of a two-column table, is not verbatim evidence. | Copy each word's definition from its own verified passage; never paraphrase. A definition may stop early only at a phrase boundary. Missing either meaning withholds the pair. |
| Explanation language (`explanation_language_errors`) | Every Cyrillic token of a learner-facing explanation (`rationale`, `rationaleUk`, `calqueSense`, `authenticSense`, and `distinction_gloss_uk` for paronym, antonym and homonym items) must be a clean VESUM form. Only an explicit `рос. …` mention, the item's own contrasted forms (calque, answer, options, corrections) and dictionary abbreviations written with their period are exempt; quotation marks are not (`Тактовний — «вежливий»` is withheld). | Replace the wording with text copied from a verified source. `--broken-validator-fixtures` proves every gate on a planted defect. |

For `normativeJudgment`, SHA-256 is computed over UTF-8 bytes after
`_normalize_source_text` in `scripts/audit/generate_practice_deck.py`:
remove U+0301 combining acute marks; join a Cyrillic word hyphenated across a
line break (including a soft hyphen); map `–`, `—`, `‑` to `-`, `«`, `»`, `“`,
`”`, `„` to `"`, and `’`, `ʼ` to `'`; collapse whitespace to one space,
trim, then Unicode `casefold()`. The source check applies this same
normalisation to the copied passage and its `sources.db` chunk. To add or
repair a frame, run this one-liner from the repository worktree once with the
exact `normativeSupport.passage` as input and once with the exact
`sentence_with_slot` as input; store the respective outputs in `passageSha256`
and `sentenceSha256`:

```bash
.venv/bin/python -c 'import hashlib, sys; from scripts.audit.generate_practice_deck import _normalize_source_text; print(hashlib.sha256(_normalize_source_text(sys.stdin.read()).encode("utf-8")).hexdigest())' < reviewed-text.txt
```

### Measured effect (2026-09-28)

All item counts in every row below come from
`batch_state/tasks/fix-8727-r4.result` (round-4 final-code, semantic-key
comparison against published deck `atlas-practice-v1-c0c3f3242b5134b6`;
key: `lemmaId`, prompt, answer, contrast). `Retained` counts published items
still emitted, `withheld` is published minus retained, and `added` counts new
items, so `final` is retained plus added. The report uses a completed
default-budget build and a focused final-code surface-budget replay; its
default-limit rerun ended before writing a deck.

| Mode | Level | Published | Retained | Withheld | Added | Final |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Heritage | A1 | 7 | 0 | 7 | 0 | 0 |
| Heritage | A2 | 44 | 7 | 37 | 0 | 7 |
| Heritage | B1 | 265 | 28 | 237 | 0 | 28 |
| Heritage | B2 | 26 | 9 | 17 | 0 | 9 |
| Heritage | C1 | 12 | 2 | 10 | 0 | 2 |
| Paronym | A1 | 22 | 2 | 20 | 0 | 2 |
| Paronym | A2 | 17 | 2 | 15 | 1 | 3 |
| Paronym | B1 | 69 | 26 | 43 | 1 | 27 |
| Paronym | B2 | 11 | 4 | 7 | 0 | 4 |
| Paronym | C1 | 5 | 0 | 5 | 0 | 0 |

The round-4 report measures withheld totals, without a per-reason item
breakdown. The independent review
(`batch_state/tasks/cf-8727-r4-claude.result`) measured 341 of 387 Heritage
frames without a `normativeJudgment`, and identified four paronym registry
pairs withheld for a missing sourced meaning for one word. These are frame
and pair counts, respectively, not allocations of the item totals above.

Heritage keeps 24 registry pairs with 46 reviewed frame judgments (counted in
`registry/lexicon/heritage_pairs.yaml`; the 46 judgments were also checked in
`batch_state/tasks/cf-8727-r4-claude.result`). Paronym keeps 20 registry rows
whose two meanings pass `paronym_gloss_provenance_errors` against
`data/sources.db` (counted in `registry/lexicon/paronym_pairs.yaml` with the
round-4 gate); they emit 36 final items across levels in the round-4 report.
The withheld rows and pairs stay in the registries for source-backed repair
(replacement work: #8329).

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
