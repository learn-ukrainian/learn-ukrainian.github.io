# Word Atlas usage-label scope

Issue: #9603. Implementation: `resolve_usage_label` in
`scripts/lexicon/heritage_classifier.py`, mirrored by `resolveUsageLabel` in
`site/src/lib/lexicon/heritage-severity.ts`.

A public usage label («русизм», «калька», «архаїзм», «діалектизм», «історизм»,
«запозичення») may describe a whole headword only with source proof of that
scope: a reviewed directional judgment for a Russianism or calque, a
dictionary marker in the headword slot for a register label. A citation, a
list membership, a stored note or a headword occurrence names where to look.
It is not evidence. Everything else stays contextual or unresolved and never
becomes a lexical condemnation of the word. An unresolved Russianism or calque
claim is neutral: no warning, and no green heritage defence either.

## Scopes

| Scope | Meaning | Browse filter | Entry page |
| --- | --- | --- | --- |
| `lemma` | Locator and excerpt bind the claim to the headword | code (`rus`, `calq`, `arch`, `dial`, `hist`, `borr`; `avoid` = bound `rus`/`calq` on an avoid-list article) | red/yellow box or register badge, locator shown |
| `sense` | Curated `kind: sense_restricted` record on this headword | none | yellow box titled for one sense, its cited sources, no headword badge |
| `phrase` | Curated `kind: phrasal` record on this headword | none | yellow box titled for a collocation, its cited sources, no headword badge |
| `reverse` | The headword is the replacement named by another form's record | none | note: direction, the record's own scope note, its references, and that no excerpt establishes the replacement |
| `unresolved` | A claim whose scope or authority the record does not establish | none | neutral notes: suggested replacements, source excerpts and the Atlas note, each marked for what it is |
| `none` | No usage claim | none | unchanged |

Without the article headword nothing binds, so no `lemma` label is returned.

## Source proof

Russianism and calque proof comes from the current curated records,
`scripts/lexicon/calque_corrections.py` and
`registry/lexicon/heritage_pairs.yaml`, never from citations copied into a
stored Atlas record. `usage_source_records` keeps, for each record and the
headword it is keyed by:

- **judgments**: a heritage pair frame's `normativeJudgment` (rejected form,
  endorsed form, sense) whose `passageSha256` or `currentNormPassageSha256`
  matches the stored `normativeSupport`/`currentNormSupport` passage at the
  same locator, digest normalised as `scripts/audit/generate_practice_deck.py`
  (`docs/practice/heritage-pairs-growth.md`). The rejected form must be the
  headword, the locator a normative chunk, and the passage still its digest;
  endorsed forms of judgments with differing senses keep their sense.
- **citations**, sense and phrase records only: a `locator: excerpt` item whose
  chunk a reviewer read in `sources.db` and bound (`SOURCE_CHECKED_CHUNKS`:
  scope, rejected form, endorsed forms with any context the passage sets,
  excerpt digest). Digest, scope and headword must match; only forms among the
  record's corrections are offered (`являтися` → `бути`), each with its source
  context (`чинний (закон)`, `активний (вулкан)`), never pooled under one sense.
  Co-occurring words or another book's locator stay an unverified reference.

A normative chunk is a `sources.db` chunk id of Антоненко-Давидович «Як ми
говоримо» (`antonenko-davydovych-yak-my-hovorymo_p031`), Караванський,
Волощак, or a school textbook by Авраменко, Заболотний, Глазова, Литвинова or
Ворон (`9-klas-ukrajinska-mova-avramenko-2017_s0159`). Source names
(`Антоненко-Давидович`), author-grade citations (`voron-9`), UA-GEC,
Грінченко and other sources name no passage and admit nothing. A normative
locator plus a headword occurrence admits nothing either: a paragraph that
mentions the word without correcting it is not a correction.

`scripts/audit/generate_search_index.py` writes this view into
`site/src/data/lexicon-browse-meta.json` as `usageSources`
(`schema: atlas-usage-sources.v1`) with the SHA-256 of both inputs. Browse
uses it directly. Entry pages read it through `usageSourceProof` in
`heritage-severity.ts`. Both judge every stored record by it: a stored
locator that the current record no longer cites (`являтися`, `s0162` →
`s0159`) is never shown as a source. A record that the current data no longer
proves keeps its stored scope with no authority.

## Russianism or calque for the whole word

The curated record (the current one, else the stored `curated_calque` or a
`calque_warning` with `kind`) must have `kind: lexical` and a judgment whose
rejected form is the headword. `participle` names a word-formation type, not
a scope (the `діючий` record is sense-split). Any other or missing kind is
unresolved (`curated_kind_without_scope`); a lexical record without a
judgment is unresolved (`no_headword_bound_evidence`).

The record is `rus` when `is_russianism` is set on a non-authentic
classification. Otherwise it is `calq`. The red or yellow box names the
judgment locators and quotes the judged passage. Sense and phrase records keep
their contextual scope. Their authority lists judgment and citation locators.
Without either, the box says no normative source binds the caution and lists
the record's references.

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
   (`garbage діал.`) does not count. A label (`заст.`, `діал.`, `іст.`, whole
   tokens) in its headword slot, before the first sense, binds. A label after a
   sense number (`ДИВАН … 1. іст.`), a homonym index (`ДИВАН ²`, `ДИВАН²`,
   `I … II …`) or an unlabelled headword does not.
2. **ЕСУМ historical witness.** The marker must sit in the headword slot of
   an attestation of the same word, followed by a «gloss»
   (`гридь (іст.) «нижча верхівка княжої дружини»`) or a parenthesised
   explanation (`тіун (іст.) (назва ряду службових осіб на Русі …)`). That
   gloss must share a content word (five or more letters) with the article's
   gloss, so the marker describes the article's referent. Markers on
   derivatives (`гридниця (іст.)`), cognates (`п. діал.`), other words,
   quotations, nested brackets or another referent do not bind. The locator is
   shown (`ЕСУМ, т. 1, с. 592`).
3. **Both.** Archaism and dialect describe current register, which the modern
   card decides: an unlabelled card outweighs an ЕСУМ `заст.`/`діал.` marker
   (`платівка`: ЕСУМ 4:431 `заст.`, СУМ-20 unmarked, «патефонна платівка»).
   A historism names a historical referent, which an unlabelled single-sense
   card does not contradict, so the ЕСУМ witness binds. A card with homonyms
   or several senses (`1.`, `2.`) limits it to one sense. The overruled or
   limited witness stays visible as a note with its locator and marker
   (`source_marker_not_whole_word`).

Грінченко and VESUM tags remain attestations. Unbound register
classifications are unresolved. The entry page says the Atlas could not tie
the classification to a source marker for this word and sense. It does not
claim the source lacks one, and it does not guess where a marker belongs.

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
- Unresolved notes keep replacements (a source's only with source proof, else
  Atlas suggestions), the record's unchecked citations and the Atlas note.
- An editorial `avoid:` gloss (`слідуючий`) or an embedded `(Russian calque; standard Ukrainian: …)`
  clause (`переключити`) is verbatim only with a lemma-bound Russianism or calque (`міроприємство`).
  Otherwise the entry header, translation, page description, course-phrase gloss, browse and search
  show the meaning with a qualified Atlas note (`displayGloss`). A historism badge names its source marker
  (`Історизм · ЕСУМ, т. 1, с. 592`) and claims nothing about current usage.
- Atlas prose stored with a record (`noteUk`, `note`, `detail`) is
  commentary. Every box and style note marks it as not confirmed by a source
  excerpt, so a scoped caution never carries a broader unsourced claim
  (`неділя`: the duration caution is sourced, the stored «лише сьомий день»
  wording is not).

## Producer and projection

- `compute_warning_severity(…, headword=…)` derives `russianism_red` and
  `calque_yellow` only from the scoped label. An unresolved claim is `none`,
  not `treasured`. `classification` and `is_russianism` (the V7 gate inputs)
  are unchanged.
- The classifier and `enrich_manifest._curated_calque` carry `evidence` and
  the digest-bound `judgments` into the stored record. The producer resolves
  its own fresh record. An explicit heritage-pair `kind` replaces the
  `participle` default.
- `scripts/audit/generate_search_index.py` (`classification_code`) and the
  entry model never trust stored `warning_severity` or `classification` on
  their own. They re-resolve every stored record, including stale ones, with
  the article headword, gloss, definition cards and the `usageSources`
  projection.
- Source observations (`attestations`, `reverse_calques`, curated notes) are
  preserved and rendered as notes.
