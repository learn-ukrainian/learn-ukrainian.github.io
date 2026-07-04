# Word Atlas POC Route Map

The legacy Word Atlas POC has been split into one design source per HTML file.
Each file is the single source for the route or route variant listed here.

| HTML file | Route | Preserved source view |
| --- | --- | --- |
| `landing.html` | `/lexicon/` | Original default `князь` Word Atlas surface |
| `detail.html` | `/lexicon/{lemma}` | `прапор` lemma detail with Soviet-definition warning |
| `heritage-defense.html` | `/lexicon/файний` | `файний` heritage-defense detail variant |

All three files share `word-atlas.css`, which contains the light/dark `--lu-*`
tokenized styles extracted from the original POC. The legacy top-level POC path
is kept as a short compatibility stub for existing links.

## Entry Model Alignment

The route map predates the finalized entry model in
[`docs/runbooks/word-atlas-entry-model.md`](../../runbooks/word-atlas-entry-model.md).
Implementation must treat `/lexicon/{slug}` as an Atlas entry route, not as a
lemma-only route. The current POC covers lemma-style articles only; the next
design pass must add at least one expression-like detail view before shipping
first-class `expression`, `phraseologism`, `proverb`, or `multiword_term`
article support.

Required future POC coverage:

| Missing design source | Route | Entry model surface |
| --- | --- | --- |
| `expression-detail.html` or equivalent | `/lexicon/{slug}` | Fixed formula, idiom/proverb, or multiword term article with component lemma backlinks |

## Drift Prevention

- POC route map changes and implementation route changes must land together.
- Any supported `entry_type` must have a named article template or an explicit
  documented reason it reuses another template.
- Public search and status APIs must count approved article entries separately
  from alias/form records.
- Expression-like pages must show component lemma cross-links without rendering
  broken public links.
- POC docs may show aggregate counts and invented examples, but must not include
  private source text, private paths, raw textbook snippets, private Ohoiko
  content, or candidate lemma lists.
