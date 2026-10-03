# Word Atlas usage-label scope

Issue: #9603. Implementation: `resolve_usage_label` in
`scripts/lexicon/heritage_classifier.py`, mirrored by `resolveUsageLabel` in
`site/src/lib/lexicon/heritage-severity.ts`.

A public usage label («русизм», «калька», «архаїзм», «діалектизм», «історизм»,
«запозичення») may describe a whole headword only when the stored heritage
record names an authority and carries evidence that the authority's claim
covers the headword itself. Everything else stays contextual or unresolved. It
never becomes a lexical condemnation of the word.

## Scopes

| Scope | Meaning | Browse filter | Entry page |
| --- | --- | --- | --- |
| `lemma` | Named authority, claim covers the headword | code (`rus`, `calq`, `arch`, `dial`, `hist`, `borr`) | red/yellow box or register badge, authority shown |
| `sense` | Curated `kind: sense_restricted` record on this headword | none | yellow box titled for one sense, no headword badge |
| `phrase` | Curated `kind: phrasal` record on this headword | none | yellow box titled for a collocation, no headword badge |
| `reverse` | The headword is the recommended replacement of a calque | none | style note naming the calque, never a warning |
| `unresolved` | Warning or label without a named lemma-scoped authority | none | neutral style note; raw attestations unchanged |
| `none` | No usage claim | none | unchanged (heritage defence may still show) |

`primary_source: surzhyk_to_avoid` keeps the browse `avoid` code and the red
entry box. The authority is the article's own provenance.

## What counts as lemma-level evidence

**Russianism or calque.** A curated record (`curated_calque`, or a
`calque_warning` carrying `kind`) whose kind is neither `sense_restricted` nor
`phrasal` (those kinds are contextual), and whose `source`/`citations` name a
normative authority:

- Антоненко-Давидович «Як ми говоримо» (`antonenko*`, slovnyk.me `davydov`);
- Караванський (`karavansk*`);
- Волощак (`voloshchak`, `voloschak`);
- a named school textbook id (`avramenko|zabolotnyi|glazova|litvinova|voron-<grade>`).

The record is `rus` when `is_russianism` is set on a non-authentic
classification. Otherwise it is `calq`.

None of these is a normative authority on its own: UA-GEC annotations,
Грінченко attestations, explanatory dictionaries, LanguageTool suggestions,
Штепа's purist replacements, classifier output, bare family names
(`state-standard`, `slovnyk-dicts`, `legacy-manifest`), replacement similarity,
VESUM membership and a Russian morphological shadow.

**Archaism, dialect or historism.** These are register claims about modern
usage. Only a modern explanatory dictionary card in the article binds them:
СУМ-20, else ВТС. The label (`заст.`, `діал.`, `іст.`, matched as whole
tokens) must sit in the headword slot, before the first sense. These cases do
not bind:

- a label after a sense number (`ДИВАН … 1. іст.`);
- a homonym-indexed card (`ДИВАН ²`, `I … II …`);
- a card whose headword is unlabelled (`ГОРОД, а, ч. Ділянка …`).

ЕСУМ, Грінченко and VESUM tags remain attestations. Their markers may belong
to one sense, a cognate (`п. діал.`), an OCR column, an older homonym
(`трактувати (заст.) «частувати»`), or a quotation substring (`хвіст.` is not
`іст.`).

**Borrowing.** This is an etymological claim. The ЕСУМ entry for the same
headword must state the borrowing (`запозич…`).

Precedence: a bound register label wins over a curated Russianism, keeping
authentic heritage first. An unbound register classification never hides a
named lexical calque.

## Producer and projection

- `compute_warning_severity` derives `russianism_red`/`calque_yellow` only from
  the scoped label. Reverse calques, bare replacement suggestions and Russian
  shadows never raise a warning. `classification` and `is_russianism` (the
  V7 gate inputs) are unchanged.
- `scripts/audit/generate_search_index.py` (`classification_code`) and the
  entry model never trust stored `warning_severity` or `classification` on
  their own. They re-resolve every stored record, including stale ones.
- Source observations (`attestations`, `reverse_calques`, curated notes) are
  preserved and rendered as notes.
