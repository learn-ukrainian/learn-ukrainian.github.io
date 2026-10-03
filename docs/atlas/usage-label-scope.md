# Word Atlas usage-label scope

Issue: #9603. Implementation: `resolve_usage_label` in
`scripts/lexicon/heritage_classifier.py`, mirrored by `resolveUsageLabel` in
`site/src/lib/lexicon/heritage-severity.ts`.

A public usage label («русизм», «калька», «архаїзм», «діалектизм», «історизм»,
«запозичення») may describe a whole headword only when the stored record holds
a source locator and an excerpt from that source that binds the claim to this
headword. A citation, a list membership or a stored note names where to look.
It is not evidence. Everything else stays contextual or unresolved and never
becomes a lexical condemnation of the word. An unresolved Russianism or calque
claim is neutral: no warning, and no green heritage defence either.

## Scopes

| Scope | Meaning | Browse filter | Entry page |
| --- | --- | --- | --- |
| `lemma` | Locator and excerpt bind the claim to the headword | code (`rus`, `calq`, `arch`, `dial`, `hist`, `borr`; `avoid` = bound `rus`/`calq` on an avoid-list article) | red/yellow box or register badge, locator shown |
| `sense` | Curated `kind: sense_restricted` record on this headword | none | yellow box titled for one sense, no headword badge |
| `phrase` | Curated `kind: phrasal` record on this headword | none | yellow box titled for a collocation, no headword badge |
| `reverse` | The headword is the replacement named by another form's record | none | note: direction, the record's own scope note, its references, and that no excerpt establishes the replacement |
| `unresolved` | A claim whose scope or authority the record does not establish | none | neutral notes: suggested replacements, source excerpts and the Atlas note, each marked for what it is |
| `none` | No usage claim | none | unchanged |

Without the article headword nothing binds, so no `lemma` label is returned.

## Russianism or calque for the whole word

All of these must hold:

- the curated record (`curated_calque`, or a `calque_warning` with `kind`) has
  `kind: lexical`. `participle` names a word-formation type, not a scope (the
  `діючий` record is sense-split). Any other or missing kind is unresolved
  (`curated_kind_without_scope`);
- one evidence item has a normative locator: Антоненко-Давидович (style guide
  id, `antonenko-…`, `Антоненко-Давидович`), Караванський, Волощак, or a school
  textbook chunk (`<grade>-klas-…-<author>-<year>_s…` for Авраменко, Заболотний,
  Глазова, Литвинова, Ворон). Author-grade citations like `voron-9` are not
  locators;
- the item's excerpt has at least four words and names the headword. Words of
  six or more letters may appear inflected (`міроприємства`); shorter words and
  multiword headwords must match exactly.

Evidence items are `normative_support` / `current_norm_support`
(`{locator, passage}`) and `evidence` strings of the form `locator: excerpt`.
A bare citation (`antonenko:Бажаючий`), an excerpt about the Russian etymon or
the replacement (`следующий — тут: наступний`), a non-normative source or a
missing headword binds nothing (`no_headword_bound_evidence`).

The record is `rus` when `is_russianism` is set on a non-authentic
classification. Otherwise it is `calq`. Sense and phrase records keep their
contextual scope. Their authority lists only bound excerpts. Without one, the
box says no normative source binds the caution and lists the record's
references.

`primary_source: surzhyk_to_avoid` is provenance, not authority. It turns a
bound `rus`/`calq` into the browse code `avoid` and the red box. Alone, it
gives a neutral note only.

UA-GEC annotations, Грінченко attestations, explanatory dictionaries,
LanguageTool suggestions, Штепа's purist replacements, classifier output,
replacement similarity, VESUM membership and a Russian morphological shadow
are never normative authority.

## Archaism, dialect or historism

These are register claims. Each source keeps its evidential role:

1. **Modern explanatory card for the same headword** (СУМ-20, else ВТС). The
   card's leading headword must be the article's headword (`card_headword_matches`).
   A card for another word (`ВОЗНИЙ` on `живий`) or malformed text
   (`garbage діал.`) does not count. When such a card exists, it decides. A
   label (`заст.`, `діал.`, `іст.`, whole tokens) in its headword slot, before
   the first sense, binds. A label after a sense number (`ДИВАН … 1. іст.`), a
   homonym index (`ДИВАН ²`, `ДИВАН²`, `I … II …`) or an unlabelled headword
   does not.
2. **ЕСУМ historical witness**, only when no such modern card exists. The
   marker must sit in the headword slot of an attestation of the same word
   (`гридь (іст.) «нижча верхівка княжої дружини»`). Its gloss must share a
   content word (five or more letters) with the article's gloss, so the marker
   describes the article's referent. Markers on derivatives (`гридниця (іст.)`),
   cognates (`п. діал.`), other words, quotations or another referent do not
   bind. The locator is shown (`ЕСУМ, т. 1, с. 592`).

Грінченко and VESUM tags remain attestations. Unbound register
classifications are unresolved. The entry page says the classification is not
confirmed by a headword label. It does not guess where the source's marker
belongs.

**Borrowing** is an etymological claim. The ЕСУМ entry for the same headword
must state the borrowing (`запозич…`).

Precedence: a bound register label wins over a curated Russianism, keeping
authentic heritage first. An unbound register classification never hides a
bound lexical calque.

## Visible wording

- The green box describes evidence, not origin. VESUM attests a form's
  morphology only. The box is «Засвідчена українська форма» and lists each
  attesting source with its role. It never says «питома». A bound register
  label is titled by its register and quotes the headword-slot excerpt and
  locator.
- Reverse notes keep the record's direction (`X` as replacement for `Y`), its
  scope note (the `чинний` law/volcano split) and its references. They state
  that no normative excerpt establishes the replacement or its extent.
- Unresolved notes keep suggested replacements, source excerpts (with their
  locators) and the Atlas note, which is marked as not confirmed by a source
  excerpt.

## Producer and projection

- `compute_warning_severity(…, headword=…)` derives `russianism_red` and
  `calque_yellow` only from the scoped label. An unresolved claim is `none`,
  not `treasured`. `classification` and `is_russianism` (the V7 gate inputs)
  are unchanged.
- The classifier and `enrich_manifest._curated_calque` carry the binding
  excerpts (`evidence`, heritage-pair `normativeSupport`/`currentNormSupport`)
  into the stored record. An explicit heritage-pair `kind` replaces the
  `participle` default.
- `scripts/audit/generate_search_index.py` (`classification_code`) and the
  entry model never trust stored `warning_severity` or `classification` on
  their own. They re-resolve every stored record, including stale ones, with
  the article headword, gloss and definition cards.
- Source observations (`attestations`, `reverse_calques`, curated notes) are
  preserved and rendered as notes.
