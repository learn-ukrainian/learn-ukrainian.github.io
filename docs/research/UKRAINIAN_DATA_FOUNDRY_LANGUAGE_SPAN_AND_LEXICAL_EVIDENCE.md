# Ukrainian Data Foundry: Language-Span and Lexical-Evidence Contract

> **Status:** Evidence record and implementation contract
> **Owner:** [#6121](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6121)
> under the [#6056 Ukrainian Data Foundry epic](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6056)
> **Recorded:** 2026-08-01
> **Scope:** Russian, Ukrainian-phonetic Russian, mixed-language, historical,
> quoted, and lexically unresolved spans
> **Does not authorize:** correction gold, model training, dataset release,
> bulk dictionary redistribution, or automatic rewriting of source text

## Foundry outcome

This contract advances the project's North Star: give Ukrainian and open-model
teams reproducible infrastructure for teaching models modern literary
Ukrainian without erasing literary truth, historical language, regional
variation, or multilingual context. Its concrete output is a span-aware
evidence layer that can feed separately governed training, correction,
preference, and evaluation views.

The implementation priority is therefore not to maximize the number of tokens
labeled “Ukrainian” or “Russian.” It is to produce auditable decisions that
help a model avoid Russian interference, surzhyk-like generation, bad grammar,
and calqued phrasing while retaining legitimate Ukrainian forms and source
fidelity.

## Decisions

1. Preserve every source byte. Detection adds offsets, evidence, and a
   disposition; it never rewrites the canonical corpus.
2. Detect and classify spans, not isolated tokens. Language identity,
   representation, discourse role, and downstream use are separate axes.
3. Keep faithful literary and modern-normative training views separate.
   Russian quotations and stylized speech stay in the former; they are masked
   from loss or excluded from the latter.
4. Treat a VESUM miss as a routing event, not an error verdict. Escalate an
   encountered form through Ukrainian sources before condemnation.
5. Use `r2u` as strong positive evidence for Russian lemmas and Ukrainian
   alternatives, but not as proof that a shared surface is Russian in context.
6. Treat `slovnyk.me` as an aggregator. Retain the underlying dictionary,
   period, register, URL, evidence kind, and rights posture for every result.
7. Use the Ukrainian Lingua-Information Fund (ULIF) synonym module as
   sense- and register-aware correction evidence after its existing adapter
   passes fail-closed parser and rights tests.
8. Only qualified Ukrainian-human adjudication may turn a candidate into a
   correction or preference record. Evaluation gold remains excluded.

These decisions record the operator's direction and Oleksiy's recommendation
to use the ULIF synonym tab. They refine the approved Foundry architecture;
they do not create a new data source or authorize external outreach.

## Why token-only classification fails

The full-corpus profiler processed 189,150 records and 50,298,925 lexical
words. It recorded 9,292,022 VESUM-unknown token occurrences representing
1,091,066 distinct normalized forms. These values measure lookup coverage,
not errors or Russian content.

The aggregate receipt records `что` 25,567 times: 25,406 in literary text, 74
in external articles, 45 in public textbooks, and 42 in Ukrainian Wikipedia.
Short, locator-bound corpus inspection found materially different uses:

| Phenomenon | Corpus locator | Bounded evidence | Required initial disposition |
| --- | --- | --- | --- |
| Russian historical quotation in modern scholarship | `literary/6cadb199_c0081` | `что вызвало смуту` | `russian_standard` + `quotation` |
| Russian character dialogue in modern Ukrainian prose | `literary/6bb17922_c0033` | `они что, не разговаривают?` | `russian_standard` + `dialogue` |
| Ukrainian-phonetic representation of Russian speech | `literary/0d122682_c0003` | `Вот, что значіт цівілізація!` | `russian_phonetic_rendering` + `dialogue` |
| Longer Ukrainian-phonetic Russian span | `literary/aff207b0_c0049` | `очєнь вєжліви с нєй` | `russian_phonetic_rendering` + `dialogue` |
| Older East Slavic continuum evidence | `literary/f82cfba8_c0202` | `что вас порушило` | `historical_unresolved`, not modern-error gold |

The table is a routing demonstration, not completed linguistic adjudication.
The source period, work, surrounding span, attribution, and human review remain
part of the final decision.

## Measured lexical-tool behavior

The following results were reproduced on 2026-08-01 through the repository's
`sources` MCP and pinned VESUM snapshot. `Russian shadow` is the existing
`pymorphy3`-based suspicion signal.

| Surface | VESUM | Russian shadow | Direct `r2u` | Evidence consequence |
| --- | --- | --- | --- | --- |
| `что` | absent | match, 1.0 | found | Strong standard-Russian candidate; context still determines role. |
| `значіт` | absent | no match, 0.423 | not found | Direct token checks miss Ukrainian-phonetic Russian. Candidate `значит` is found by `r2u`. |
| `цівілізація` | absent | no match, 0.570 | not found | Candidate `цивилизация` is found by `r2u` with Ukrainian `цивілізація`. |
| `очєнь` | `adv:slang` | no match | not found | VESUM presence does not prove the surrounding span is Ukrainian; candidate `очень` is found by `r2u`. |
| `вєжліви` | absent | no match, 0.458 | not found | Candidate `вежливы` is found by `r2u`. |
| `нєй` | absent | match, 1.0 | not found | One strong token may anchor a longer phonetic-Russian span. |
| `придєт` | absent | no match, 0.423 | not found | Candidate `придёт` is found by `r2u`. |
| `врємя` | absent | no match, 0.600 | not found | Candidate `время` is found by `r2u`. |
| `перекличка` | absent | match, 1.0 | not decisive | False Russian suspicion: ЕСУМ and СУМ-20 attest authentic Ukrainian usage. |

This evidence establishes two non-negotiable rules:

- a single Ukrainian or Russian dictionary lookup cannot classify a span; and
- phonetic-Russian detection requires bounded candidate reconstruction before
  Russian morphology and `r2u` can validate the reconstructed form.

Candidate reconstruction must be gated by an already suspicious span. Global
letter substitutions such as `і → и` or `є → е` would corrupt Ukrainian and
are prohibited.

## Four independent span axes

### Language identity

- `ukrainian`
- `russian`
- `mixed_ukrainian_russian`
- `historical_east_slavic_unresolved`
- `church_slavonic_candidate`
- `other_language`
- `uncertain`

### Representation

- `standard_orthography`
- `ukrainian_phonetic_rendering_of_russian`
- `historical_orthography`
- `transliteration`
- `ocr_or_encoding_candidate`
- `unknown`

### Discourse role

- `narration`
- `quotation`
- `dialogue`
- `epigraph`
- `title`
- `citation_or_document`
- `metalinguistic_example`
- `unknown`

### Downstream disposition

- `retain_faithful`
- `retain_with_language_metadata`
- `mask_from_modern_ukrainian_loss`
- `exclude_from_modern_ukrainian_view`
- `correction_candidate`
- `protected_historical_or_register_variation`
- `human_review_required`
- `unresolved`

No axis implies another. Russian dialogue is not an authorial error. A
historical span is not automatically Russian. An unquoted Russian form in a
modern model response may be a correction candidate, but only after contextual
and human review.

## Evidence routing

### 1. Segment structure before lexical judgment

Identify bounded candidate spans using guillemets, quotation marks, dash-led
dialogue, paragraph boundaries, epigraph/title structure, document citations,
and metalinguistic framing. Punctuation is evidence, not a complete solution:
literary dialogue may use dashes, and a language switch may occur inside one
sentence.

### 2. Gather Ukrainian evidence

For each token and reconstructed lemma:

1. Query VESUM for form, lemma, POS, paradigm, and usage markers.
2. Split hyphenated and appositive compounds before condemning a miss.
3. Query ULIF paradigms when the VESUM form is absent or ambiguous.
4. Query `search_heritage` for historical, dialectal, regional, and inherited
   Ukrainian evidence.
5. Query `slovnyk.me` sources and corpus attestation for unresolved forms.

Positive Ukrainian evidence prevents a bare Russian-shadow result from
becoming a Russianism verdict. `перекличка` is the regression case: it is
absent from VESUM and receives a 1.0 Russian-shadow score, but ЕСУМ and
[СУМ-20 through `slovnyk.me`](https://slovnyk.me/dict/newsum/%D0%BF%D0%B5%D1%80%D0%B5%D0%BA%D0%BB%D0%B8%D1%87%D0%BA%D0%B0)
attest it as Ukrainian.

### 3. Gather Russian evidence

Use Russian-only orthographic signals, the existing Russian morphological
analyser, `r2u`, and high-precision Russian function-word sequences. A direct
`r2u` result is positive Russian lexical evidence and supplies possible
Ukrainian equivalents; it does not establish contextual exclusivity for a
surface shared by both languages.

### 4. Reconstruct Ukrainian-phonetic Russian conservatively

Generate a small, scored set of possible standard-Russian forms only when at
least one of these gates is satisfied:

- the surrounding span contains a high-confidence Russian anchor;
- several adjacent VESUM-unknown tokens jointly map to Russian lemmas;
- quotation/dialogue structure and the source context support a language
  switch; or
- qualified review has marked the span for phonetic-Russian analysis.

Validate every reconstructed candidate with Russian morphology and `r2u`.
Record the original surface, reconstructed candidate, transformation path,
score, and evidence. Do not overwrite the original.

### 5. Decode a span, not a bag of tokens

Combine adjacent token evidence with period, register, work, discourse role,
and script/orthography evidence. Isolated weak tokens remain unresolved. A
coherent sequence such as `значіт цівілізація` or `придєт наше врємя` may be
classified as a phonetic-Russian candidate even when most individual tokens
miss the Russian-shadow threshold.

### 6. Preserve uncertainty for adjudication

The detector emits evidence and a proposed span label. It cannot emit
correction gold. Qualified Ukrainian reviewers confirm the language/function
classification and decide whether any modern-narration or generated-output
case should become a correction record.

## Source responsibilities and rights posture

| Source | Proper role | Must not be treated as |
| --- | --- | --- |
| VESUM | Ukrainian form, lemma, POS, paradigm, and usage-marker evidence | Meaning, contextual language identity, or sentence correctness |
| `r2u` | Russian lemma evidence and Ukrainian equivalent candidates | A contextual Russian-only verdict for shared forms |
| Russian morphology | Inflectional recognition and Russian-lemma candidates | A verdict that overrides Ukrainian or heritage attestation |
| ULIF DictUA | Ukrainian register, paradigms, synonym sense groups, antonyms, and phraseology | Automatically redistributable training data |
| `slovnyk.me` | Per-dictionary Ukrainian attestation and definition/style evidence | One homogeneous dictionary or bulk-open dataset |
| `search_heritage` | Defense of authentic archaism, historism, dialect, regionalism, and inherited vocabulary | Automatic modern-standard admission |
| Ukrainian corpus | Context, collocation, period, register, and discourse evidence | Rights permission or correctness by raw frequency |
| Qualified humans | Contextual decision, alternatives, rationale, and conflict resolution | A substitute for lineage, rights, or contamination checks |

### ULIF evidence

The official [ULIF system description](https://lcorp.ulif.org.ua/pdf/Pro_Systemu.pdf)
states that the online system has inflection, synonymy, antonymy, and
phraseology modules. Its synonym module is based on the two-volume *Словник
синонімів української мови* (1999–2000), contains about 9,200 synonym series,
and preserves semantic, grammatical, stylistic, and contextual distinctions.

The repository already implements:

- WebForms state replay and the `paradigm`, `synonyms`, `antonyms`, and
  `phraseology` sections in `scripts/rag/source_query.py`;
- structured relation-group parsing in
  `scripts/lexicon/runner/ulif_dictua_parse.py`; and
- a sequential one-second fetch policy in
  `scripts/lexicon/runner/fetch_ulif_20k.py`.

An initial live `query_ulif("дуже", sections=["paradigm", "synonyms"])` probe
returned structured synonym groups, register labels, citations, and content
hash `94da3fd742d98c87849f84fd90cf6b50c7cd31b9fc241d890ca74cb2d8c1da0b`,
but parser version `ulif-dictua-v1` incorrectly assigned aggregate status
`parse_error` because the adverb had no inflection table. Issue #6121 resolved
that false requirement in `ulif-dictua-v2`. A live repeat over the same content
hash returned `status: ok`, four synonym groups, and no paradigm, as expected.
Missing WebForms state, malformed result lists, incomplete tab traversal, and
transient failures still fail closed. The executable boundary and verification
commands are in the
[correction-factory runbook](../runbooks/ukrainian-data-foundry-correction-factory.md).

The inspected landing page displays `© ULIF, 2001–2026`; no explicit open-data
license for bulk redistribution was found there, and `/robots.txt` returned
HTTP 403 during the probe. This is not a legal conclusion. It is a fail-closed
admission rule:

- throttled per-lemma/internal evidence queries may retain attribution and
  response hashes;
- existing raw caches remain internal and require a scope-specific rights
  audit before reuse;
- raw HTML, quotations, and a bulk synonym graph do not enter a public dataset
  or training export without explicit permission; and
- public artifacts retain bounded source references and derived human
  decisions, not the ULIF database.

### `slovnyk.me` evidence

`slovnyk.me` is a transport and aggregation surface. Every result must retain
its underlying dictionary slug and scope. For example:

- СУМ-20: modern lexical/definitional evidence;
- the Franko dictionary: authorial and historical evidence;
- the Lviv slang dictionary: regional/marked-register evidence;
- Holoskevych 1929: historical orthographic evidence;
- Antonenko-Davydovych: Russianism and style evidence.

These sources cannot be collapsed into a Boolean `valid_ukrainian`. The
existing per-query tool contract prohibits a bulk crawl and public cache; #6121
uses it only after local deterministic filters have reduced the unresolved
candidate set.

## Derived views

### Faithful literary view

Retain original text and span offsets, including Russian quotations, character
speech, phonetic Russian, historical language, and uncertainty. This view
supports literary fidelity and language-contact research; its existence does
not authorize redistribution.

### Modern literary Ukrainian view

Use only admitted records. Preserve the surrounding Ukrainian where possible,
but mask Russian spans from language-model loss. If the target trainer cannot
consume loss masks, exclude the mixed sentence or record according to a
versioned threshold and retain an exclusion receipt. Do not replace quotation
content with silent machine translation.

### Correction and preference view

Use modern-narration or generated-output cases only after provenance, rights,
contamination, and qualified human review. A record retains:

- original context and exact span offsets;
- language, representation, discourse-role, and period labels;
- Russian lemma/reconstruction evidence and `r2u` candidates;
- Ukrainian VESUM, ULIF, `slovnyk.me`, heritage, and corpus evidence;
- accepted correction or acceptable alternatives;
- reviewer qualifications, independent decisions, conflict state, rationale,
  and uncertainty; and
- destination-specific export disposition.

## #6121 acceptance evidence

The correction factory is not complete until tests and receipts cover:

1. Standard Russian quotation preserved and masked, not “corrected.”
2. Dash-led Russian dialogue classified without requiring guillemets.
3. `значіт цівілізація` reconstructed and routed as a phonetic-Russian span.
4. `очєнь` not accepted as Ukrainian narration merely because VESUM tags it
   `slang`.
5. An older `что` span protected from automatic modern-error classification.
6. `перекличка` rescued from a VESUM miss and Russian-shadow false positive by
   Ukrainian evidence.
7. A shared Ukrainian/Russian surface protected from a bare `r2u` hit.
8. ULIF synonym groups retaining sense, register, citations, provenance, hash,
   parser status, and incomplete-tab failures.
9. `slovnyk.me` results retaining underlying dictionary identities.
10. Evaluation-source, exact-duplicate, near-duplicate, rights, and private-data
    exclusions remaining fail closed.
11. Byte-stable span and evidence receipts over identical inputs.
12. No automatic correction labels from a detector, dictionary, model, or
    aggregate vote.

## Reproduction pointers

- Full-corpus counts and top unknown forms:
  `data/projects/open_model_data/profiles/full_corpus_profile_v1.json`.
- Profiler configuration:
  `data/projects/open_model_data/profiles/public_external_full_corpus_v1.json`.
- VESUM and Russian-shadow interfaces:
  `scripts/verification/vesum.py` and
  `scripts/verification/check_ru_morph.py`.
- ULIF live adapter: `scripts/rag/source_query.py`.
- ULIF structured parser:
  `scripts/lexicon/runner/ulif_dictua_parse.py`.
- Existing durable fetch lane:
  `scripts/lexicon/runner/fetch_ulif_20k.py`.
- Ukrainian authority and escalation rules:
  `agents_extensions/shared/rules/ukrainian-linguistics.md`.

The next implementation begins from this contract. It must not rediscover or
silently simplify these distinctions.
